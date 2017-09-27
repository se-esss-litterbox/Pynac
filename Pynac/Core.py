"""
The primary module for Pynac.
"""
import subprocess as subp
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor
import os
import shutil
import glob
from collections import namedtuple
import warnings
from IPython.display import display
import ipywidgets as widgets
from ipywidgets import HBox, VBox, Layout, Box
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.io import show, push_notebook, curdoc, curstate
from Pynac.DataClasses import Param, SingleDimPS, CentreOfGravity
import Pynac.Elements as pyEle
import Pynac.Plotting as pynPlt


class Pynac(object):
    """
    The primary entry point for performing simulations.  Objects of this class
    contain all the necessary information to perform a Dynac simulation, as well
    as methods to manipulate the lattice, and to make the call to Dynac.
    """
    _DEBUG = False
    _fieldData = {
        'INPUT': 2,
        'RDBEAM': 5,
        'BMAGNET': 4,
        'FSOLE': 2,
        'SECORD': 0,
        'RASYN': 0,
        'EDFLEC': 2,
        'FIRORD': 0,
        'CAVMC': 2,
        'CAVNUM': 2,
        'FIELD': 2,
        'RWFIELD': 0,
        'HARM': 3,
        'EGUN': 2,
        'RFQPTQ': 3,
        'TILT': 2,
        'RANDALI': 2,
        'WRBEAM': 2,
        'EMIT': 0,
        'EMITGR': 3,
        'ENVEL': 4,
        'PROFGR': 3,
        'STOP': 0,
        'ZONES': 2,
        'T3D': 0
    }

    def __init__(self, filename=None):
        if filename:
            self.filename = filename
            with open(self.filename, 'r') as file:
                self.rawData = [' '.join(line.split()) for line in file]
                if self._DEBUG:
                    print("rawData:")
                    print(self.rawData)
            self._parse()

    @classmethod
    def from_lattice(cls, name, lattice):
        pyn = cls()
        pyn.name = name
        pyn.lattice = lattice
        return pyn

    def run(self):
        """
        Run the simulation in the current directory.
        """
        self._start_dynac_proc(stdin=subp.PIPE, stdout=subp.PIPE)
        str2write = self.name + '\r\n'
        if self._DEBUG:
            with open('pynacrun.log', 'a') as f:
                f.write(str2write)
        self.dynacProc.stdin.write(str2write.encode())  # The name field
        for pynEle in self.lattice:
            try:
                ele = pynEle.dynacRepresentation()
            except AttributeError:
                ele = pynEle
            str2write = ele[0]
            if self._DEBUG:
                with open('pynacrun.log', 'a') as f:
                    f.write(str2write + '\r\n')
            try:
                self.dynacProc.stdin.write((str2write + '\r\n').encode())
            except IOError:
                break
            for datum in ele[1]:
                str2write = ' '.join([str(i) for i in datum])
                if self._DEBUG:
                    with open('pynacrun.log', 'a') as f:
                        f.write(str2write+'\r\n')
                try:
                    self.dynacProc.stdin.write((str2write+'\r\n').encode())
                except IOError:
                    break
        self.dynacProc.stdin.close()
        if self.dynacProc.wait() != 0:
            raise RuntimeError("Errors occured during execution of Dynac")

    def get_x_inds(self, *dynac_type):
        """
        Return the indices into the lattice list attribute of elements whose Dynac
        type matches the input string.  Multiple input strings can be given, either
        as a comma-separated list or as a genuine Python list.
        """
        return [i for i, x in enumerate(self.lattice) for y in dynac_type if dynac_from_ele(x) == y]

    def get_x_objs(self, *dynac_type):
        """
        Return the indices into the lattice list attribute of elements whose Dynac
        type matches the input string.  Multiple input strings can be given, either
        as a comma-separated list or as a genuine Python list.
        """
        return [i for i in self.lattice for y in dynac_type if dynac_from_ele(i) == y]

    def get_plot_inds(self):
        """
        Return the indices into the lattice list attribute of elements that result
        in Dynac plot output.
        """
        return self.get_x_inds('EMITGR', 'ENVEL', 'PROFGR')

    def get_num_plots(self):
        """
        Return the number of Dynac plots that will be output when Dynac is run.
        """
        return len(self.get_plot_inds()) + 2 * len(self.get_x_inds('ENVEL'))

    def set_new_rdbeam_file(self, filename):
        """
        Change the current ``RDBEAM`` command to point at another Dynac input file.
        This will raise an IndexError if the lattice doesn't contain an RDBEAM
        command.
        """
        self.lattice[self.get_x_inds('RDBEAM')[0]][1][0][0] = filename

    def _start_dynac_proc(self, stdin, stdout):
        # self.dynacProc = subp.Popen(['dynacv6_0','--pipe'], stdin=stdin, stdout=stdout)
        self.dynacProc = subp.Popen(
            ['dynacv6_0', '--pipe'],
            stdin=stdin,
            stdout=stdout,
            stderr=subp.PIPE
        )
        if b'Error' in self.dynacProc.stdout.readline():
            raise RuntimeError('Installed version of Dynac should be upgraded to support the --pipe flag')

    def _loop(self, item):
        print(item)
        self.dynacProc.stdin.write(item[0] + '\r\n')
        for data in item[1]:
            self.dynacProc.stdin.write(data)

    def _parse(self):
        self.lattice = []
        self.name = self.rawData[0]

        ind = 1
        while ind < len(self.rawData):
            if not (self.rawData[ind] == '' or self.rawData[ind][0] == ';'):
                ind = self._parsed_chunk(ind)
                if self._DEBUG:
                    print(self.lattice[-1])
            ind += 1

    def _parsed_chunk(self, current_ind):
        dynac_str = self.rawData[current_ind]
        try:
            num_fields = self._fieldData[dynac_str]
        except KeyError:
            if dynac_str == 'GEBEAM':
                num_fields = self._get_num_fields_from_itwiss(current_ind)
            elif dynac_str == 'SCDYNAC':
                num_fields = self._get_num_fields_from_iscsp(current_ind)
            else:
                num_fields = 1
        data_str = [self.rawData[current_ind + i + 1] for i in range(num_fields)]
        dat = []
        for term in data_str:
            try:
                if self._might_be_number(term):
                    dat.append([float(term)])
                else:
                    dat.append([int(term)])
            except ValueError:
                try:
                    dat.append([float(i) if self._might_be_number(i) else int(i) for i in term.split(' ')])
                except ValueError:
                    dat.append([term])
        self.lattice.append(ele_from_pynac([dynac_str, dat]))
        return current_ind + num_fields

    def _get_num_fields_from_itwiss(self, ind):
        i_twiss = self.rawData[ind+1].split()[1]
        return {'1': 6, '0': 4}[i_twiss]

    def _get_num_fields_from_iscsp(self, ind):
        iscsp = self.rawData[ind+1]
        return {
            '1': 3,
            '-1': 6,
            '2': 3,
            '3': 3 if self.rawData[ind+3] == '0' else 4
        }[iscsp]

    def _might_be_number(self, thing):
        return ('.' in thing) or ('e' in thing) or ('E' in thing)


class Builder:
    def __init__(self):
        self.inputBeamLattice = None
        self.firstPlotDone = False

    def build_a_beam(self):
        beta_x = widgets.FloatSlider(
            value=7.5,
            min=0.01,
            max=20.0,
            step=0.01,
            description='beta_x:',
            disabled=False,
            continuous_update=False,
        )
        alpha_x = widgets.FloatSlider(
            value=0.0,
            min=-5.0,
            max=5.0,
            step=0.01,
            description='alpha_x:',
            disabled=False,
            continuous_update=False,
        )
        emit_x = widgets.FloatSlider(
            value=0.5,
            min=0.01,
            max=10.0,
            step=0.01,
            description='emit_x:',
            disabled=False,
            continuous_update=False,
        )
        beta_y = widgets.FloatSlider(
            value=7.5,
            min=0.01,
            max=20.0,
            step=0.01,
            description='beta_y:',
            disabled=False,
            continuous_update=False,
        )
        alpha_y = widgets.FloatSlider(
            value=0.0,
            min=-5.0,
            max=5.0,
            step=0.01,
            description='alpha_y:',
            disabled=False,
            continuous_update=False,
        )
        emit_y = widgets.FloatSlider(
            value=0.5,
            min=0.01,
            max=10.0,
            step=0.01,
            description='emit_y:',
            disabled=False,
            continuous_update=False,
        )
        beta_z = widgets.FloatSlider(
            value=7.5,
            min=0.01,
            max=20.0,
            step=0.01,
            description='beta_z:',
            disabled=False,
            continuous_update=False,
        )
        alpha_z = widgets.FloatSlider(
            value=0.0,
            min=-5.0,
            max=5.0,
            step=0.01,
            description='alpha_z:',
            disabled=False,
            continuous_update=False,
        )
        emit_z = widgets.FloatSlider(
            value=500,
            min=1.0,
            max=1000.0,
            step=1.0,
            description='emit_z:',
            disabled=False,
            continuous_update=False,
        )

        label_layout = widgets.Layout(width='100%')
        twiss_x_label = widgets.Label(value="Horizontal Twiss", layout=label_layout)
        twiss_y_label = widgets.Label(value="Vertical Twiss", layout=label_layout)
        twiss_z_label = widgets.Label(value="Longitudinal Twiss", layout=label_layout)

        energy_offset = widgets.FloatText(value=0.0, display='flex', width='20%')
        x_offset = widgets.FloatText(value=0.0, display='flex', width='20%')
        xp_offset = widgets.FloatText(value=0.0, display='flex', width='20%')
        y_offset = widgets.FloatText(value=0.0, display='flex', width='20%')
        yp_offset = widgets.FloatText(value=0.0, display='flex', width='20%')
        phase_offset = widgets.FloatText(value=0.0, display='flex', width='20%')

        energy_offset_label = widgets.Label(value="Energy Offset (MeV):", layout=label_layout)
        x_offset_label = widgets.Label(value="x Offset (cm):", layout=label_layout)
        xp_offset_label = widgets.Label(value="xp Offset (mrad):", layout=label_layout)
        y_offset_label = widgets.Label(value="y Offset (cm):", layout=label_layout)
        yp_offset_label = widgets.Label(value="yp Offset (mrad):", layout=label_layout)
        phase_offset_label = widgets.Label(value="Phase Offset (s):", layout=label_layout)

        beam_freq = widgets.IntText(value=352.21e6, display='flex', flex_basis='20%')
        bunch_population = widgets.IntText(value=1000, display='flex', flex_basis='20%')
        self.bunchPopulation = bunch_population

        beam_freq_label = widgets.Label(value="Beam Freq (Hz):", layout=label_layout)
        bunch_population_label = widgets.Label(value="Bunch pop.:", layout=label_layout)

        rest_mass = widgets.FloatText(value=938.27231, display='flex', flex_basis='20%')
        atomic_num = widgets.FloatText(value=1, display='flex', flex_basis='20%')
        charge = widgets.FloatText(value=1, display='flex', flex_basis='20%')

        rest_mass_label = widgets.Label(value="Rest mass (MeV/c^2):", layout=label_layout)
        atomic_num_label = widgets.Label(value="Atomic Number:", layout=label_layout)
        charge_label = widgets.Label(value="Particle Charge:", layout=label_layout)

        def get_pynac_input():
            beam = ['GEBEAM', [
                [4, 1],
                [beam_freq.value, bunch_population.value],
                [energy_offset.value, x_offset.value,
                    xp_offset.value, y_offset.value,
                    yp_offset.value, phase_offset.value,
                 ],
                [alpha_x.value, beta_x.value, emit_x.value],
                [alpha_y.value, beta_y.value, emit_y.value],
                [alpha_z.value, beta_z.value, emit_z.value],
            ]]
            return beam

        def get_dynac_input():
            beam = 'GEBEAM\r\n'
            beam += '4 1\r\n'
            beam += '%e %d\r\n' % (beam_freq.value, bunch_population.value)
            beam += '%f %f %f %f %f %f\r\n' % (energy_offset.value, x_offset.value, xp_offset.value,
                                               y_offset.value, yp_offset.value, phase_offset.value)
            beam += '%f %f %f\r\n' % (alpha_x.value, beta_x.value, emit_x.value)
            beam += '%f %f %f\r\n' % (alpha_y.value, beta_y.value, emit_y.value)
            beam += '%f %f %f' % (alpha_z.value, beta_z.value, emit_z.value)
            return beam

        css_height_str = '170px'
        view_btn = widgets.Button(description="View Pynac Input")
        pynac_view_area = widgets.Textarea()
        pynac_view_area.layout.height = css_height_str
        dynac_view_area = widgets.Textarea()
        dynac_view_area.layout.height = css_height_str

        pynac_view_area.value = get_pynac_input().__str__()
        dynac_view_area.value = get_dynac_input()

        self.inputBeamLattice = []
        self.inputBeamLattice.append(get_pynac_input())
        self.inputBeamLattice.append(['INPUT', [[938.27231, 1.0, 1.0], [3.6223537, 0.0]]])
        self.inputBeamLattice.append(['REFCOG', [[0]]])
        self.inputBeamLattice.append(['EMITGR', [
            ['Generated Beam'],
            [0, 9],
            [0.5, 80.0, 0.5, 80.0, 0.5, 0.5, 50.0, 1.0]
        ]])
        self.inputBeamLattice.append(['STOP', []])

        test = Pynac.from_lattice("Zero-length lattice for beam generation", self.inputBeamLattice)
        test.run()

        with open('emit.plot') as f:
            for i in range(204):
                f.readline()
            num_parts = int(f.readline())
            x, xp = [], []
            for i in range(num_parts):
                dat = f.readline().split()
                x.append(float(dat[0]))
                xp.append(float(dat[1]))
            f.readline()
            for i in range(202):
                f.readline()
            y, yp = [], []
            for i in range(num_parts):
                dat = f.readline().split()
                y.append(float(dat[0]))
                yp.append(float(dat[1]))
            f.readline()
            for i in range(203):
                f.readline()
            z, zp = [], []
            for i in range(num_parts):
                dat = f.readline().split()
                z.append(float(dat[0]))
                zp.append(float(dat[1]))

        data_source = ColumnDataSource(data=dict(x=x, xp=xp, y=y, yp=yp, z=z, zp=zp))

        p0 = figure(plot_height=250, plot_width=296, y_range=(-5, 5), x_range=(-1, 1))
        p0.xaxis.axis_label = 'Horizontal position'
        p0.yaxis.axis_label = 'Horizontal angle'
        p0.circle('x', 'xp', color="#2222aa", alpha=0.5, line_width=2, source=data_source)

        p1 = figure(plot_height=250, plot_width=296, y_range=(-5, 5), x_range=(-1, 1))
        p1.xaxis.axis_label = 'Vertical position'
        p1.yaxis.axis_label = 'Vertical angle'
        p1.circle('y', 'yp', color="#2222aa", alpha=0.5, line_width=2, source=data_source, name="foo")

        p2 = figure(plot_height=250, plot_width=296, y_range=(-0.1, 0.1), x_range=(-150, 150))
        p2.xaxis.axis_label = 'Longitudinal phase'
        p2.yaxis.axis_label = 'Longitudinal energy'
        p2.circle('z', 'zp', color="#2222aa", alpha=0.5, line_width=2, source=data_source, name="foo")

        grid = gridplot([[p0, p1, p2]])
        self.beamBuilderPlotHandle = show(grid, notebook_handle=True)
        self.beamBuilderPlotDoc = curdoc()
        push_notebook(document=self.beamBuilderPlotDoc, handle=self.beamBuilderPlotHandle)

        def on_button_clicked(_):
            pynac_view_area.value = get_pynac_input().__str__()
            dynac_view_area.value = get_dynac_input()
            self.inputBeamLattice[0] = get_pynac_input()
            self.inputBeamLattice[0][1][1][1] = 1000
            zero_length_lattice = Pynac.from_lattice("Zero-length lattice for beam generation", self.inputBeamLattice)
            zero_length_lattice.run()
            with open('emit.plot') as f:
                for i in range(204):
                    f.readline()
                num_parts = int(f.readline())
                x, xp = [], []
                for i in range(num_parts):
                    dat = f.readline().split()
                    x.append(float(dat[0]))
                    xp.append(float(dat[1]))
                f.readline()
                for i in range(202):
                    f.readline()
                y, yp = [], []
                for i in range(num_parts):
                    dat = f.readline().split()
                    y.append(float(dat[0]))
                    yp.append(float(dat[1]))
                f.readline()
                for i in range(203):
                    f.readline()
                z, zp = [], []
                for i in range(num_parts):
                    dat = f.readline().split()
                    z.append(float(dat[0]))
                    zp.append(float(dat[1]))
            data_source.data['x'] = x
            data_source.data['xp'] = xp
            data_source.data['y'] = y
            data_source.data['yp'] = yp
            data_source.data['z'] = z
            data_source.data['zp'] = zp
            push_notebook(document=self.beamBuilderPlotDoc, handle=self.beamBuilderPlotHandle)

        active_widget_list = [beta_x, alpha_x, emit_x, beta_y, alpha_y, emit_y, beta_z, alpha_z, emit_z,
                              energy_offset, x_offset, xp_offset, y_offset, yp_offset, phase_offset,
                              beam_freq, bunch_population, rest_mass, atomic_num, charge
                              ]
        for slider in active_widget_list:
            slider.observe(on_button_clicked)

        pynac_box_label = widgets.Label(value="Pynac Input", layout=label_layout)
        dynac_box_label = widgets.Label(value="Dynac Input", layout=label_layout)

        twiss_controls = HBox([
                VBox([twiss_x_label, beta_x, alpha_x, emit_x]),
                VBox([twiss_y_label, beta_y, alpha_y, emit_y]),
                VBox([twiss_z_label, beta_z, alpha_z, emit_z]),
            ])
        col_layout = Layout(display='flex', flex_flow='column', align_items='stretch')
        other_controls = Box([
                Box([rest_mass_label, atomic_num_label, charge_label, beam_freq_label, bunch_population_label],
                    layout=col_layout),
                Box([rest_mass, atomic_num, charge, beam_freq, bunch_population], layout=col_layout),
                Box([energy_offset_label, x_offset_label, xp_offset_label,
                     y_offset_label, yp_offset_label, phase_offset_label], layout=col_layout),
                Box([energy_offset, x_offset, xp_offset, y_offset, yp_offset, phase_offset], layout=col_layout),
            ], layout=Layout(
                    display='flex',
                    flex_flow='row',
                    align_items='stretch',
                    width='100%'
        ))

        input_text = HBox([
                VBox([pynac_box_label, pynac_view_area]),
                VBox([dynac_box_label, dynac_view_area])
            ])

        accordion = widgets.Accordion(children=[twiss_controls, other_controls, input_text])
        accordion.set_title(0, 'Twiss (to alter the phase-space plots)')
        accordion.set_title(1, 'Beam details (will not alter the phase-space plots)')
        accordion.set_title(2, "Pynac/Dynac input (to copy'n'paste into your own files)")
        display(accordion)

    def run_simulation(self):
        self.sim = None

        load_lattice_btn = widgets.Button(
            description="Load lattice file",
            button_style='success',
            disabled=False,
        )
        add_built_beam = widgets.Button(
            description="Add new beam",
            button_style='',
            disabled=True,
        )
        self.addBuiltBeam = add_built_beam
        run_sim_btn = widgets.Button(
            description="Run simulation",
            button_style='',
            disabled=True,
        )
        plot_btn = widgets.Button(
            description="Plot!",
            button_style='',
            disabled=True,
        )
        plotit_btn = widgets.Button(
            description="Dynac-style plotit",
            button_style='',
            disabled=True,
        )

        buttons = HBox([load_lattice_btn, add_built_beam, run_sim_btn, plotit_btn])
        display(buttons)

        def load_lattice_click(_):
            self.sim = Pynac('ESS_with_SC_ana.in')
            if self.inputBeamLattice:
                add_built_beam.disabled = False
                add_built_beam.button_style = 'warning'
            run_sim_btn.disabled = False
            run_sim_btn.button_style = 'danger'
        load_lattice_btn.on_click(load_lattice_click)

        def add_built_beam_click(_):
            beam_inds = self.sim.get_x_inds('RDBEAM')
            beam_inds += self.sim.get_x_inds('REFCOG')
            beam_inds += self.sim.get_x_inds('INPUT')
            beam_inds += self.sim.get_x_inds('GEBEAM')
            beam_inds = sorted(beam_inds, reverse=True)
            for ele in beam_inds:
                del self.sim.lattice[ele]
            self.sim.lattice = self.inputBeamLattice[:3] + self.sim.lattice
        add_built_beam.on_click(add_built_beam_click)

        def run_sim_click(_):
            plotit_btn.disabled = True
            plotit_btn.button_style = ''
            self.sim.run()
            plotit_btn.disabled = False
            plotit_btn.button_style = 'warning'
        run_sim_btn.on_click(run_sim_click)

        def plotit_btn_click(_):
            if not self.firstPlotDone:
                self.plotitTool = pynPlt.NewPynPlt()
                self.plotitTool.parseAndOrganise()
                self.handle0 = self.plotitTool.plotEMITGR(0)
                # self.handle1 = self.plotitTool.plotENVEL(0)
                self.firstPlotDone = True
            else:
                self.plotitTool.parseAndOrganise()
                # push_notebook(handle=self.handle0)
                push_notebook(handle=self.handle1)
                # for p in self.plotitTool.plotHandleDict['emitgrHandle']:
                #     push_notebook(handle=p)
                # for p in self.plotitTool.plotHandleDict['envelHandle']:
                #     push_notebook(handle=p)
                # for p in self.plotitTool.plotHandleDict['profgrHandle']:
                #     push_notebook(handle=p)
        plotit_btn.on_click(plotit_btn_click)


class PhaseSpace:
    """
    A representation of the phase space of the simulated bunch read from the
    ``dynac.short`` file.  Each of the phase space parameters is represented as a
    ``elements.Parameter`` namedtuple.

    This class is intended to be used in interactive explorations of the data
    produced during Pynac simulations.
    """
    def __init__(self, data_str_matrix):
        self.dataStrMatrix = data_str_matrix
        self.xPhaseSpace = self._get_ps_from_line(5)
        self.yPhaseSpace = self._get_ps_from_line(6)
        self.zPhaseSpace = self._get_ps_from_line(4)
        self.COG = CentreOfGravity(
            x=Param(val=float(self.dataStrMatrix[1][0]), unit='mm'),
            xp=Param(val=float(self.dataStrMatrix[1][1]), unit='mrad'),
            y=Param(val=float(self.dataStrMatrix[1][2]), unit='mm'),
            yp=Param(val=float(self.dataStrMatrix[1][3]), unit='mrad'),
            KE=Param(val=float(self.dataStrMatrix[0][3]), unit='MeV'),
            TOF=Param(val=float(self.dataStrMatrix[0][4]), unit='deg'),
        )
        self.particlesLeft = Param(val=float(self.dataStrMatrix[4][5]), unit='num')

    def _get_ps_from_line(self, num):
        try:
            test = float(self.dataStrMatrix[num][6])
            return SingleDimPS(
                pos=Param(val=float(self.dataStrMatrix[num][0]), unit='mm'),
                mom=Param(val=float(self.dataStrMatrix[num][1]), unit='mrad'),
                R12=Param(val=float(self.dataStrMatrix[num][2]), unit='?'),
                normEmit=Param(val=float(self.dataStrMatrix[num][3]), unit='mm.mrad'),
                nonNormEmit=Param(val=float(self.dataStrMatrix[num][6]), unit='mm.mrad'),
            )
        except IndexError:
            return SingleDimPS(
                mom=Param(val=float(self.dataStrMatrix[num][1]), unit='keV'),
                pos=Param(val=float(self.dataStrMatrix[num][0]), unit='deg'),
                R12=Param(val=float(self.dataStrMatrix[num][2]), unit='?'),
                normEmit=Param(val=float(self.dataStrMatrix[num][3]), unit='keV.ns'),
                nonNormEmit=Param(val=None, unit=None),
            )

    def __repr__(self):
        repr_str = 'COG: ' + self.COG.__repr__()
        repr_str += '\nparticles left: ' + self.particlesLeft.__repr__()
        repr_str += '\nx: ' + self.xPhaseSpace.__repr__()
        repr_str += '\ny: ' + self.yPhaseSpace.__repr__()
        repr_str += '\nz: ' + self.zPhaseSpace.__repr__()
        return repr_str


def make_phase_space_list():
    """
    Extract all the phase space information (due to ``EMIT`` commands in the input
    file), and create a list of PhaseSpace objects.  The primary purpose of this
    is for interactive explorations of the data produced during Pynac simulations.
    """
    with open('dynac.short') as f:
        data_str = ''.join(line for line in f.readlines())
        data_str_array = data_str.split('beam (emit card)')[1:]
        data_str_matrix = [[j.strip().split() for j in i] for i in[chunk.split('\n')[1:8] for chunk in data_str_array]]

        return [PhaseSpace(data) for data in data_str_matrix]


def get_number_of_particles():
    """
    Queries the ``dynac.short`` file for the number of particles used in the
    simulation.
    """
    with open('dynac.short') as f:
        data_str = ''.join(line for line in f.readlines())
        num_of_parts = int(data_str.split('Simulation with')[1].strip().split()[0])
    return num_of_parts


def dynac_from_ele(ele):
    try:
        dyn_str = ele.dynacRepresentation()[0]
    except AttributeError:
        dyn_str = ele[0]
    return dyn_str


def ele_from_pynac(pynac_repr):
    try:
        constructor = getattr(pyEle, pyEle._dynac2pynac[pynac_repr[0]])
        obj = constructor.from_dynacRepr(pynac_repr)
    except AttributeError:
        obj = pynac_repr
    return obj


def multi_process_pynac(file_list, pynac_func, num_iters=100, max_workers=8):
    """
    Use a ProcessPool from the ``concurrent.futures`` module to execute ``num_iters``
    number of instances of ``pynac_func``.  This function takes advantage of ``do_single_dynac_process``
    and ``pynac_in_sub_directory``.
    """
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        tasks = [executor.submit(do_single_dynac_process, num, file_list, pynac_func) for num in range(num_iters)]
    exc = [task.exception() for task in tasks if task.exception()]
    if exc:
        return exc
    else:
        return "No errors encountered"


def do_single_dynac_process(num, filelist, pynac_func):
    """
    Execute ``pynac_func`` in the ``pynac_in_sub_directory`` context manager.  See the
    docstring for that context manager to understand the meaning of the ``num`` and
    ``filelist`` inputs.

    The primary purpose of this function is to enable multiprocess use of Pynac via
    the ``multi_process_pynac`` function.
    """
    with pynac_in_sub_directory(num, filelist):
        pynac_func()


@contextmanager
def pynac_in_sub_directory(num, file_list):
        """
        A context manager to create a new directory, move the files listed in ``file_list``
        to that directory, and change to that directory before handing control back to
        context.  The closing action is to change back to the original directory.

        The directory name is based on the ``num`` input, and if it already exists, it
        will be deleted upon entering the context.

        The primary purpose of this function is to enable multiprocess use of Pynac via
        the ``multi_process_pynac`` function.
        """
        print('Running %d' % num)
        new_dir = 'dynacProc_%04d' % num
        if os.path.isdir(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        for f in file_list:
            shutil.copy(f, new_dir)
        os.chdir(new_dir)

        yield

        os.chdir('..')
