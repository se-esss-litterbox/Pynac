class Pynac(object):
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
    
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'r') as file:
            self.rawData = [' '.join(line.split()) for line in file]
        self._parse()
    
    def run(self):
        self._startDynacProc(stdin=subp.PIPE, stdout=subp.PIPE)
        self.dynacProc.stdin.write(self.name + '\r\n') # The name field
        for ele in self.lattice:
            self.dynacProc.stdin.write(ele[0] + '\r\n')
            for datum in ele[1]:
                self.dynacProc.stdin.write(' '.join([str(i) for i in datum]) + '\r\n')
        return self.dynacProc.communicate()
    
    def getXinds(self, *X):
        return [i for i,x in enumerate(self.lattice) for y in X if x[0] == y]
    
    def getPlotInds(self):
        return self.getXinds('EMITGR','ENVEL','PROFGR')
    
    def getNumPlots(self):
        return len(self.getPlotInds()) + 2 * len(self.getXinds('ENVEL'))
    
    def setNewRDBEAMfile(self, filename):
        self.lattice[a.getXinds('RDBEAM')[0]][1][0][0] = filename
    
    def _startDynacProc(self, stdin, stdout):
        self.dynacProc = subp.Popen(
            ['./dynacv6_0','--pipe'], 
            stdin=stdin, 
            stdout=stdout,
            stderr=subp.PIPE
        )
    
    def _loop(self, item):
        print item
        self.dynacProc.stdin.write(item[0] + '\r\n')
        for data in item[1]:
            self.dynacProc.stdin.write(data)
    
    def _parse(self):
        self.lattice = []
        self.name = self.rawData[0]
        
        ind = 1
        while ind < len(self.rawData):
            if not (self.rawData[ind] == '' or self.rawData[ind][0] == ';'):
                ind = self._parsedChunk(ind)
            ind += 1
    
    def _parsedChunk(self, currentInd):
        dynacStr = self.rawData[currentInd]
        try:
            numFields = self._fieldData[dynacStr]
        except KeyError:
            if dynacStr == 'GEBEAM':
                numFields = self._getNumFieldsFromiTwiss(currentInd)
            elif dynacStr == 'SCDYNAC':
                numFields = self._getNumFieldsFromISCSP(currentInd)
            else:
                numFields = 1
        dataStr = [self.rawData[currentInd+i+1] for i in range(numFields)]
        dat = []
        for term in dataStr:
            try:
                if self._mightBeNumber(term):
                    dat.append([float(term)])
                else:
                    dat.append([int(term)])
            except ValueError:
                try:
                    dat.append([float(i) if self._mightBeNumber(i) else int(i) for i in term.split(' ')])
                except ValueError:
                    dat.append([term])
        self.lattice.append([dynacStr, dat])
        return currentInd + numFields
    
    def _getNumFieldsFromiTwiss(self, ind):
        iTwiss = self.rawData[ind+1].split()[1]
        return {'1': 6, '0': 4}[iTwiss]
    
    def _getNumFieldsFromISCSP(self, ind):
        iscsp = self.rawData[ind+1]
        return {
            '1': 3,
            '-1': 6,
            '2': 3,
            '3': 3 if self.rawData[ind+3]=='0' else 4
        }[iscsp]
    
    def _mightBeNumber(self, thing):
        return ('.' in thing) or ('e' in thing) or ('E' in thing)

