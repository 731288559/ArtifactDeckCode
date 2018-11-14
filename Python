import base64
import struct

# Basic Deck decoder
class MyArtifactDeckDecoder:
    def __init__(self):
        self.s_nCurrentVersion = 2
        self.sm_rgchEncodedPrefix = 'ADC'

    # returns dict("heroes" : array[id, turn], "cards" : array[id, count], "name" : name)
    def ParseDeck(self, strDeckCode):
        # print 'raw : %s' % strDeckCode
        deckBytes = self.DecodeDeckString(strDeckCode)
        if not deckBytes:
            return False
        # print deckBytes
        deck = self.ParseDeckInternal(strDeckCode, deckBytes)
        return deck

    def DecodeDeckString(self, strDeckCode):
        # check for prefix
        if strDeckCode[:len(self.sm_rgchEncodedPrefix)] != self.sm_rgchEncodedPrefix:
            return False
        # strip prefix from deck code
        strNoPrefix = strDeckCode[len(self.sm_rgchEncodedPrefix):]
        strNoPrefix.replace('-','_').replace('/','=')

        missing_padding = 4 - len(strNoPrefix) % 4
        if missing_padding <= 4:
            strNoPrefix += b'=' * missing_padding
        decoded = base64.b64decode(strNoPrefix)
        r = struct.unpack('%dB' % len(decoded),decoded)
        # print r
        return r

    # reads out a var-int encoded block of bits, returns true if another chunk should follow
    def ReadBitsChunk(self, nChunk, nNumBits, nCurrShift, nOutBits):
        nContinueBit = 1 << nNumBits
        nNewBits = nChunk & ( nContinueBit - 1 )
        nOutBits |= ( nNewBits << nCurrShift )

        flag = True if ( nChunk & nContinueBit ) != 0 else False
        return flag, nOutBits

    def ReadVarEncodedUint32(self, nBaseValue, nBaseBits, data, indexStart, indexEnd, outValue):
        outValue = 0

        nDeltaShift = 0
        flag,outValue = self.ReadBitsChunk(nBaseValue, nBaseBits, nDeltaShift, outValue)
        if ( nBaseBits == 0 ) or flag:
            nDeltaShift += nBaseBits

            while True:
                # do we have more room?
                if indexStart > indexEnd:
                    print 'err 1'
                    return False, indexStart, outValue

                # read the bits from this next byte and see if we are done
                nNextByte = data[indexStart]
                indexStart += 1
                flag, outValue = self.ReadBitsChunk(nNextByte, 7, nDeltaShift, outValue)
                if not flag:
                    break
                nDeltaShift += 7

        return True, indexStart, outValue

    # handles decoding a card that was serialized
    def ReadSerializedCard(self, data, indexStart, indexEnd, nPrevCardBase, nOutCount, nOutCardID):
        # end of the memory block?
        if indexStart > indexEnd:
            print 'err 2'
            return False, indexStart, nPrevCardBase, nOutCount, nOutCardID

        # header contains the count (2 bits), a continue flag, and 5 bits of offset data. If we have 11 for the count bits we have the count
		# encoded after the offset
        nHeader = data[indexStart]
        indexStart += 1
        bHasExtendedCount = ( ( nHeader >> 6 ) == 0x03 )

        # read in the delta, which has 5 bits in the header, then additional bytes while the value is set
        nCardDelta = 0
        flag, indexStart, nCardDelta = self.ReadVarEncodedUint32(nHeader, 5, data, indexStart, indexEnd, nCardDelta)
        if not flag:
            print 'err 3'
            return False, indexStart, nPrevCardBase, nOutCount, nOutCardID

        nOutCardID = nPrevCardBase + nCardDelta

        # now parse the count if we have an extended count
        if bHasExtendedCount:
            flag, indexStart, nOutCount = self.ReadVarEncodedUint32(0, 0, data, indexStart, indexEnd, nOutCount)
            if not flag:
                print 'err 4'
                return False, indexStart, nPrevCardBase, nOutCount, nOutCardID
        else:
            # the count is just the upper two bits + 1 (since we don't encode zero)
            nOutCount = ( nHeader >> 6 ) + 1
            
        # update our previous card before we do the remap, since it was encoded without the remap
        nPrevCardBase = nOutCardID
        return True, indexStart, nPrevCardBase, nOutCount, nOutCardID

    def ParseDeckInternal(self, strDeckCode, deckBytes):
        nCurrentByteIndex = 0
        nTotalBytes = len(deckBytes)

        # check version num
        nVersionAndHeroes = deckBytes[nCurrentByteIndex]
        nCurrentByteIndex += 1
        # print nVersionAndHeroes
        version = nVersionAndHeroes >> 4
        # print version
        if self.s_nCurrentVersion != version and version != 1:
            print 1
            return False

        # do checksum check
        nChecksum = deckBytes[nCurrentByteIndex]
        nCurrentByteIndex += 1

        nStringLength = 0
        if version > 1:
            nStringLength = deckBytes[nCurrentByteIndex]
            nCurrentByteIndex += 1
        nTotalCardBytes = nTotalBytes - nStringLength

        # grab the string size
        nComputedChecksum = 0
        # print nCurrentByteIndex,nTotalCardBytes
        for i in range(nCurrentByteIndex+1, nTotalCardBytes+1):
            nComputedChecksum += deckBytes[i-1]
        # print nComputedChecksum
        masked = nComputedChecksum & 0xFF
        # print nChecksum,masked
        if nChecksum != masked:
            print 2
            return False

        # read in our hero count (part of the bits are in the version, but we can overflow bits here
        nNumHeroes = 0
        flag, nCurrentByteIndex, nNumHeroes = self.ReadVarEncodedUint32(nVersionAndHeroes, 3, deckBytes, nCurrentByteIndex, nTotalCardBytes, nNumHeroes)
        if not flag:
            print 3
            return False

        
        # now read in the heroes
        heroes = []
        nPrevCardBase = 0
        for i in range(0, nNumHeroes):
            nHeroTurn = 0
            nHeroCardID = 0
            flag, nCurrentByteIndex, nPrevCardBase, nHeroTurn, nHeroCardID = self.ReadSerializedCard(deckBytes, nCurrentByteIndex, nTotalCardBytes, nPrevCardBase, nHeroTurn, nHeroCardID)
            if not flag:
                print 4
                return False
            item = [nHeroCardID,nHeroTurn]
            heroes.append(item)
        
        cards = []
        nPrevCardBase = 0
        while nCurrentByteIndex+1 <= nTotalCardBytes:
            nCardCount = 0
            nCardID = 0
            flag, nCurrentByteIndex, nPrevCardBase, nCardCount, nCardID = self.ReadSerializedCard(deckBytes, nCurrentByteIndex, nTotalBytes, nPrevCardBase, nCardCount, nCardID)
            if not flag:
                print 5
                return False
            item = [nCardID, nCardCount]
            cards.append(item)

        name = ''
        if nCurrentByteIndex <= nTotalBytes:
            _bytes = deckBytes[-1*nStringLength:]
            name = map(chr, _bytes)
            name = ''.join(name)
            # replace strip_tags with an HTML sanitizer or escaper as needed.
            # $name = strip_tags( $name );
            # todo
        
        result = {}
        result['heroes'] = heroes
        result['cards'] = cards
        result['name'] = name
        return result


