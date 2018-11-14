import base64
import struct
import math

# Basic Deck encoder
class MyArtifactDeckEncoder:
    def __init__(self):
        self.s_nCurrentVersion = 2
        self.sm_rgchEncodedPrefix = "ADC"
        self.sm_nMaxBytesForVarUint32 = 5
        self.knHeaderSize = 3

    # expects dict("heroes" : array(id, turn), "cards" : array(id, count), "name" : name)
	# signature cards for heroes SHOULD NOT be included in "cards"
    def EncodeDeck(self, deckContents):
        if not deckContents:
            return False
        # print deckContents
        _bytes = self.EncodeBytes(deckContents)
        # print _bytes
        if not _bytes:
            return False
        deck_code = self.EncodeBytesToString(_bytes)
        return deck_code

    def EncodeBytes(self, deckContents):
        cards = deckContents.get('cards', [])
        heroes = deckContents.get('heroes', [])
        name = deckContents.get('name', '')
        if deckContents == {} or cards == [] or heroes == []:
            return False
        
        # sort
        cards.sort(key=lambda x:x[0],reverse=False)
        heroes.sort(key=lambda x:x[0],reverse=False)

        countHeroes = len(heroes)
        allCards = heroes + cards

        _bytes = []
        # our version and hero count
        version = self.s_nCurrentVersion << 4 | self.ExtractNBitsWithCarry(countHeroes, 3)
        flag, _bytes = self.AddByte(_bytes, version)
        if not flag:
            return False
        
        # the checksum which will be updated at the end
        nDummyChecksum = 0
        nCheckssumByte = len(_bytes)
        flag, _bytes = self.AddByte(_bytes, nDummyChecksum)
        if not flag:
            return False

        # write the name size
        nameLen = 0
        if name != '':

            # replace strip_tags() with your own HTML santizer or escaper.
            # $name = strip_tags( $deckContents['name'] );
            # todo
            trimLen = len(name)
            while trimLen > 63:
                amountToTrim = math.floor((trimLen - 63) / 4 )
                amountToTrim = amountToTrim if amountToTrim > 1 else 1
				# name = mb_substr( name, 0, mb_strlen(name) - amountToTrim )
                # todo
                trimLen = len(name)
            
            nameLen = len(name)
        
        flag, _bytes = self.AddByte(_bytes, nameLen)
        if not flag:
            return False
        
        flag, _bytes = self.AddRemainingNumberToBuffer(countHeroes, 3, _bytes)
        if not flag:
            return False

        prevCardId = 0
        for i in range(0, countHeroes):
            card = allCards[i]
            if card[1] == 0:
                return False

            flag, _bytes = self.AddCardToBuffer(card[1], card[0]-prevCardId, _bytes)
            if not flag:
                return False
            
            prevCardId = card[0]
        
        # reset our card offset
        prevCardId = 0

        # now all of the cards
        for i in range(countHeroes, len(allCards)):
          # see how many cards we can group together
            card = allCards[i]
            if card[1] == 0:
                return False
            if card[0] <= 0:
                return False

            # record this set of cards, and advance
            flag, _bytes = self.AddCardToBuffer(card[1], card[0]-prevCardId, _bytes)
            if not flag:
                return False
            prevCardId = card[0]
        
        # save off the pre string bytes for the checksum
        preStringByteCount = len(_bytes)

        # write the string
        nameBytes = struct.unpack('%dB' % len(name),name)
        for nameByte in nameBytes:
            flag, _bytes = self.AddByte(_bytes, nameByte)
            if not flag:
                return False
        
        unFullChecksum, _bytes = self.ComputeChecksum(_bytes, preStringByteCount-self.knHeaderSize)
        unSmallChecksum = (unFullChecksum & 0x0FF)   

        _bytes[nCheckssumByte] = unSmallChecksum
        return _bytes

    def EncodeBytesToString(self, _bytes):
        byteCount = len(_bytes)
        # if we have an empty buffer, just return
        if byteCount == 0:
            return False

        packed = struct.pack('%dB' % len(_bytes), *_bytes)
        # print packed

        # missing_padding = 4 - len(packed) % 4
        # if missing_padding:
        #     packed += b'=' * missing_padding

        encoded = base64.b64encode(packed)
        # print encoded

        deck_string = self.sm_rgchEncodedPrefix + encoded

        fixedString = deck_string.replace('-', '_').replace('/', '=')

        return fixedString

    def ExtractNBitsWithCarry(self, value, numBits):
        unLimitBit = 1 << numBits
        unResult = (value & (unLimitBit - 1))
        if value >= unLimitBit:
            unResult |= unLimitBit

        return unResult
    
    def AddByte(self, _bytes, byte):
        if byte > 255:
            return False, _bytes
        
        _bytes.append(byte)
        return True, _bytes
    
    # utility to write the rest of a number into a buffer. This will first strip the specified N bits off,
    # and then write a series of bytes of the structure of 1 overflow bit and 7 data bits
    def AddRemainingNumberToBuffer(self, unValue, unAlreadyWrittenBits, _bytes):
        unValue >>= unAlreadyWrittenBits
        unNumBytes = 0
        while unValue > 0:
            unNextByte = self.ExtractNBitsWithCarry(unValue, 7)
            unValue >>= 7
            flag, _bytes = self.AddByte(_bytes, unNextByte)
            if not flag:
                return False, _bytes
            
            unNumBytes += 1

        return True, _bytes

    def AddCardToBuffer(self, unCount, unValue, _bytes):
        # this shouldn't ever be the case
        if unCount == 0:
            return False, _bytes
        
        countBytesStart = len(_bytes)
        # determine our count. We can only store 2 bits, and we know the value is at least one, so we can encode values 1-5. However, we set both bits to indicate an 
		# extended count encoding
        knFirstByteMaxCount = 0x03
        bExtendedCount = (unCount - 1) >= knFirstByteMaxCount

        # determine our first byte, which contains our count, a continue flag, and the first few bits of our value
        unFirstByteCount = knFirstByteMaxCount if bExtendedCount else (unCount - 1)
        unFirstByte = unFirstByteCount << 6
        unFirstByte |= self.ExtractNBitsWithCarry(unValue, 5)

        flag, _bytes = self.AddByte(_bytes, unFirstByte)
        if not flag:
            return False, _bytes
        
        # now continue writing out the rest of the number with a carry flag
        flag, _bytes = self.AddRemainingNumberToBuffer(unValue, 5, _bytes)
        if not flag:
            return False, _bytes
        
        # now if we overflowed on the count, encode the remaining count
        if bExtendedCount:
            flag, _bytes = self.AddRemainingNumberToBuffer(unCount, 0, _bytes)
            if not flag:
                return False, _bytes
        
        countBytesEnd = len(_bytes)

        if countBytesEnd - countBytesStart > 11:
            return False, _bytes
        
        return True, _bytes
    
    def ComputeChecksum(self, _bytes, unNumBytes):
        unChecksum = 0
        for i in range(self.knHeaderSize, unNumBytes+self.knHeaderSize):
            byte = _bytes[i]
            unChecksum += byte

        return unChecksum, _bytes
