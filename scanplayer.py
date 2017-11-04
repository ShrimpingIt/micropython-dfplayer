from dfplayer import Player
from utime import sleep_ms
from machine import Pin

class ScanPlayer(Player):
    def __init__(self, folders=10, scan=True, *a, **k ):
        if 'busy_pin' not in k: 
            k['busy_pin'] = Pin(0) # configure D3/GPIO0 as default busy pin
        super().__init__(*a, **k) 
        if folders > 99:
            raise AssertionError("Max 99 folders (00-99)")
        self.folders = folders
        self.tracks = None
        self.recent = {}
        if scan:
            self.scan()
        # TODO handle resetting volume after scan
    
    def scan(self):
        self.awaitconfig()
        self.volume(0.1)
        self.awaitvolume()
        self.tracks = {}
        for folderNum in range(0,self.folders): 
            for fileNum in range(0,256):                # max tracks-per-folder supported by dfplayer
                self.play(folderNum,fileNum)
                if self.playing():
                    if not(folderNum in self.tracks):
                        self.tracks[folderNum] = []
                    self.tracks[folderNum].append(fileNum)
                    continue
                else:
                    break
        self.volume(1.0) # TODO find principled way to set this, or remove volume control from scan
    
    def playNext(self, folderNum, wrap=True):
        if self.tracks is not None:
            if folderNum in self.tracks:
                files = self.tracks[folderNum]
                if folderNum in self.recent:
                    fileNum = self.recent[folderNum]
                    fileNum = (fileNum + 1)
                    if fileNum == len(files):
                        if wrap:
                            fileNum = fileNum % len(files) # increment with wraparound
                        else:
                            return False
                else:
                    fileNum = 0
                self.recent[folderNum] = fileNum
                self.play(folderNum, fileNum)
                return True
            else:
                raise AssertionError("Scan found no '{}' folder".format(folderNum))
        else:
            raise AssertionError("No scan available, run player.scan() first.")

    def finishAll(self, folderNum):
        if self.tracks is not None:
            if folderNum in self.tracks:
                folderTracks = self.tracks[folderNum]
                for trackNum in folderTracks:
                    self.finish(folderNum, trackNum)
            else:
                raise AssertionError("Scan found no '{}' folder".format(folderNum))
        else:
            raise AssertionError("No scan available, run player.scan() first.")
