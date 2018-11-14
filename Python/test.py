#coding=utf-8
import deck_decoder
import deck_encoder

url = 'ADCJWkTZX05uwGDCRV4XQGy3QGLmqUBg4GQJgGLGgO7AaABR3JlZW4vQmxhY2sgRXhhbXBsZQ__'
url = 'ADCJS0RMbgCFQGCQeB9CoGBSGVsbG8gd29ybGTljaHnu4Q_'
# print len(url)
decoder = deck_decoder.MyArtifactDeckDecoder()

cards = [[4000, 10], [4001, 3], [4002, 3]]
heroes = [[10001, 1], [10022, 1], [10023, 1], [10025, 3], [10026, 2]]
deckContents = {}
deckContents['heroes'] = heroes
deckContents['cards'] = cards
deckContents['name'] = 'Hello world'

encoder = deck_encoder.MyArtifactDeckEncoder()
url = encoder.EncodeDeck(deckContents)
print url

url = 'ADCJWkTZX05uwGDCRV4XQGy3QGLmqUBg4GQJgGLGgO7AaABR3JlZW4vQmxhY2sgRXhhbXBsZQ__'
result = decoder.ParseDeck(url)
print result
url = encoder.EncodeDeck(result)
print url
result = decoder.ParseDeck(url)
print result
url = encoder.EncodeDeck(result)
print url




