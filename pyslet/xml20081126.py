#! /usr/bin/env python

from xml.sax import make_parser, handler, SAXParseException, saxutils
import string, types
from StringIO import StringIO
import urlparse, os, os.path
from sys import maxunicode
import codecs, random
from types import *
from copy import copy

from pyslet.rfc2396 import URIFactory, URI, FileURL

xml_base='xml:base'
xml_lang='xml:lang'
xml_space='xml:space'

XML_MIMETYPES={
	'text/xml':True,
	'application/xml':True,
	'text/application+xml':True	
	}

def ValidateXMLMimeType(mimetype):
	return XML_MIMETYPES.has_key(mimetype)
	

XMLMixedContent=0
XMLElementContent=1
XMLEmpty=2
	
class XMLError(Exception): pass
class XMLFatalError(XMLError): pass
class XMLCommentError(XMLFatalError): pass

class XMLAttributeSetter(XMLError): pass
class XMLContentTypeError(XMLError): pass
class XMLIDClashError(XMLError): pass
class XMLIDValueError(XMLError): pass
class XMLMissingFileError(XMLError): pass
class XMLMissingLocationError(XMLError): pass
class XMLMixedContentError(XMLError): pass
class XMLParentError(XMLError): pass
class XMLUnimplementedError(XMLError): pass
class XMLUnexpectedError(XMLError): pass
class XMLUnexpectedHTTPResponse(XMLError): pass
class XMLUnsupportedSchemeError(XMLError): pass
class XMLValidationError(XMLError): pass
class XMLWellFormedError(XMLFatalError): pass

class XMLUnknownChild(XMLError): pass

from pyslet.unicode5 import CharClass
from pyslet import rfc2616 as http

NameStartCharClass=CharClass(u':', (u'A',u'Z'), u'_', (u'a',u'z'),
	(u'\xc0',u'\xd6'), (u'\xd8',u'\xf6'),
	(u'\xf8',u'\u02ff'), (u'\u0370',u'\u037d'), (u'\u037f',u'\u1fff'),
	(u'\u200c',u'\u200d'), (u'\u2070',u'\u218f'), (u'\u2c00',u'\u2fef'),
	(u'\u3001',u'\ud7ff'), (u'\uf900',u'\ufdcf'), (u'\ufdf0',u'\ufffd'))

NameCharClass=CharClass(NameStartCharClass, u'-', u'.', (u'0',u'9'),
	u'\xb7', (u'\u0300',u'\u036f'), (u'\u203f',u'\u2040'))

EncNameStartCharClass=CharClass((u'A',u'Z'), (u'a',u'z'))

EncNameCharClass=CharClass(u'-', u'.', (u'0',u'9'), (u'A',u'Z'), u'_', 
	(u'a',u'z'))
	
BaseCharClass=CharClass((u'A',u'Z'), (u'a',u'z'), (u'\xc0',u'\xd6'),
	(u'\xd8',u'\xf6'), (u'\xf8',u'\u0131'), (u'\u0134',u'\u013e'),
	(u'\u0141',u'\u0148'), (u'\u014a',u'\u017e'), (u'\u0180',u'\u01c3'),
	(u'\u01cd',u'\u01f0'), (u'\u01f4',u'\u01f5'), (u'\u01fa',u'\u0217'),
	(u'\u0250',u'\u02a8'), (u'\u02bb',u'\u02c1'), u'\u0386', (u'\u0388',u'\u038a'),
	u'\u038c', (u'\u038e',u'\u03a1'), (u'\u03a3',u'\u03ce'), (u'\u03d0',u'\u03d6'),
	u'\u03da', u'\u03dc', u'\u03de', u'\u03e0', (u'\u03e2',u'\u03f3'),
	(u'\u0401',u'\u040c'), (u'\u040e',u'\u044f'), (u'\u0451',u'\u045c'),
	(u'\u045e',u'\u0481'), (u'\u0490',u'\u04c4'), (u'\u04c7',u'\u04c8'),
	(u'\u04cb',u'\u04cc'), (u'\u04d0',u'\u04eb'), (u'\u04ee',u'\u04f5'),
	(u'\u04f8',u'\u04f9'), (u'\u0531',u'\u0556'), u'\u0559', (u'\u0561',u'\u0586'),
	(u'\u05d0',u'\u05ea'), (u'\u05f0',u'\u05f2'), (u'\u0621',u'\u063a'),
	(u'\u0641',u'\u064a'), (u'\u0671',u'\u06b7'), (u'\u06ba',u'\u06be'),
	(u'\u06c0',u'\u06ce'), (u'\u06d0',u'\u06d3'), u'\u06d5', (u'\u06e5',u'\u06e6'),
	(u'\u0905',u'\u0939'), u'\u093d', (u'\u0958',u'\u0961'), (u'\u0985',u'\u098c'),
	(u'\u098f',u'\u0990'), (u'\u0993',u'\u09a8'), (u'\u09aa',u'\u09b0'), u'\u09b2',
	(u'\u09b6',u'\u09b9'), (u'\u09dc',u'\u09dd'), (u'\u09df',u'\u09e1'),
	(u'\u09f0',u'\u09f1'), (u'\u0a05',u'\u0a0a'), (u'\u0a0f',u'\u0a10'),
	(u'\u0a13',u'\u0a28'), (u'\u0a2a',u'\u0a30'), (u'\u0a32',u'\u0a33'),
	(u'\u0a35',u'\u0a36'), (u'\u0a38',u'\u0a39'), (u'\u0a59',u'\u0a5c'), u'\u0a5e',
	(u'\u0a72',u'\u0a74'), (u'\u0a85',u'\u0a8b'), u'\u0a8d', (u'\u0a8f',u'\u0a91'),
	(u'\u0a93',u'\u0aa8'), (u'\u0aaa',u'\u0ab0'), (u'\u0ab2',u'\u0ab3'),
	(u'\u0ab5',u'\u0ab9'), u'\u0abd', u'\u0ae0', (u'\u0b05',u'\u0b0c'),
	(u'\u0b0f',u'\u0b10'), (u'\u0b13',u'\u0b28'), (u'\u0b2a',u'\u0b30'),
	(u'\u0b32',u'\u0b33'), (u'\u0b36',u'\u0b39'), u'\u0b3d', (u'\u0b5c',u'\u0b5d'),
	(u'\u0b5f',u'\u0b61'), (u'\u0b85',u'\u0b8a'), (u'\u0b8e',u'\u0b90'),
	(u'\u0b92',u'\u0b95'), (u'\u0b99',u'\u0b9a'), u'\u0b9c', (u'\u0b9e',u'\u0b9f'),
	(u'\u0ba3',u'\u0ba4'), (u'\u0ba8',u'\u0baa'), (u'\u0bae',u'\u0bb5'),
	(u'\u0bb7',u'\u0bb9'), (u'\u0c05',u'\u0c0c'), (u'\u0c0e',u'\u0c10'),
	(u'\u0c12',u'\u0c28'), (u'\u0c2a',u'\u0c33'), (u'\u0c35',u'\u0c39'),
	(u'\u0c60',u'\u0c61'), (u'\u0c85',u'\u0c8c'), (u'\u0c8e',u'\u0c90'),
	(u'\u0c92',u'\u0ca8'), (u'\u0caa',u'\u0cb3'), (u'\u0cb5',u'\u0cb9'), u'\u0cde',
	(u'\u0ce0',u'\u0ce1'), (u'\u0d05',u'\u0d0c'), (u'\u0d0e',u'\u0d10'),
	(u'\u0d12',u'\u0d28'), (u'\u0d2a',u'\u0d39'), (u'\u0d60',u'\u0d61'),
	(u'\u0e01',u'\u0e2e'), u'\u0e30', (u'\u0e32',u'\u0e33'), (u'\u0e40',u'\u0e45'),
	(u'\u0e81',u'\u0e82'), u'\u0e84', (u'\u0e87',u'\u0e88'), u'\u0e8a', u'\u0e8d',
	(u'\u0e94',u'\u0e97'), (u'\u0e99',u'\u0e9f'), (u'\u0ea1',u'\u0ea3'), u'\u0ea5',
	u'\u0ea7', (u'\u0eaa',u'\u0eab'), (u'\u0ead',u'\u0eae'), u'\u0eb0',
	(u'\u0eb2',u'\u0eb3'), u'\u0ebd', (u'\u0ec0',u'\u0ec4'), (u'\u0f40',u'\u0f47'),
	(u'\u0f49',u'\u0f69'), (u'\u10a0',u'\u10c5'), (u'\u10d0',u'\u10f6'), u'\u1100',
	(u'\u1102',u'\u1103'), (u'\u1105',u'\u1107'), u'\u1109', (u'\u110b',u'\u110c'),
	(u'\u110e',u'\u1112'), u'\u113c', u'\u113e', u'\u1140', u'\u114c', u'\u114e',
	u'\u1150', (u'\u1154',u'\u1155'), u'\u1159', (u'\u115f',u'\u1161'), u'\u1163',
	u'\u1165', u'\u1167', u'\u1169', (u'\u116d',u'\u116e'), (u'\u1172',u'\u1173'),
	u'\u1175', u'\u119e', u'\u11a8', u'\u11ab', (u'\u11ae',u'\u11af'),
	(u'\u11b7',u'\u11b8'), u'\u11ba', (u'\u11bc',u'\u11c2'), u'\u11eb', u'\u11f0',
	u'\u11f9', (u'\u1e00',u'\u1e9b'), (u'\u1ea0',u'\u1ef9'), (u'\u1f00',u'\u1f15'),
	(u'\u1f18',u'\u1f1d'), (u'\u1f20',u'\u1f45'), (u'\u1f48',u'\u1f4d'),
	(u'\u1f50',u'\u1f57'), u'\u1f59', u'\u1f5b', u'\u1f5d', (u'\u1f5f',u'\u1f7d'),
	(u'\u1f80',u'\u1fb4'), (u'\u1fb6',u'\u1fbc'), u'\u1fbe', (u'\u1fc2',u'\u1fc4'),
	(u'\u1fc6',u'\u1fcc'), (u'\u1fd0',u'\u1fd3'), (u'\u1fd6',u'\u1fdb'),
	(u'\u1fe0',u'\u1fec'), (u'\u1ff2',u'\u1ff4'), (u'\u1ff6',u'\u1ffc'), u'\u2126',
	(u'\u212a',u'\u212b'), u'\u212e', (u'\u2180',u'\u2182'), (u'\u3041',u'\u3094'),
	(u'\u30a1',u'\u30fa'), (u'\u3105',u'\u312c'), (u'\uac00',u'\ud7a3'))

CombiningCharClass=CharClass((u'\u0300',u'\u0345'), (u'\u0360',u'\u0361'),
	(u'\u0483',u'\u0486'), (u'\u0591',u'\u05a1'), (u'\u05a3',u'\u05b9'),
	(u'\u05bb',u'\u05bd'), u'\u05bf', (u'\u05c1',u'\u05c2'), u'\u05c4',
	(u'\u064b',u'\u0652'), u'\u0670', (u'\u06d6',u'\u06e4'), (u'\u06e7',u'\u06e8'),
	(u'\u06ea',u'\u06ed'), (u'\u0901',u'\u0903'), u'\u093c', (u'\u093e',u'\u094d'),
	(u'\u0951',u'\u0954'), (u'\u0962',u'\u0963'), (u'\u0981',u'\u0983'), u'\u09bc',
	(u'\u09be',u'\u09c4'), (u'\u09c7',u'\u09c8'), (u'\u09cb',u'\u09cd'), u'\u09d7',
	(u'\u09e2',u'\u09e3'), u'\u0a02', u'\u0a3c', (u'\u0a3e',u'\u0a42'),
	(u'\u0a47',u'\u0a48'), (u'\u0a4b',u'\u0a4d'), (u'\u0a70',u'\u0a71'),
	(u'\u0a81',u'\u0a83'), u'\u0abc', (u'\u0abe',u'\u0ac5'), (u'\u0ac7',u'\u0ac9'),
	(u'\u0acb',u'\u0acd'), (u'\u0b01',u'\u0b03'), u'\u0b3c', (u'\u0b3e',u'\u0b43'),
	(u'\u0b47',u'\u0b48'), (u'\u0b4b',u'\u0b4d'), (u'\u0b56',u'\u0b57'),
	(u'\u0b82',u'\u0b83'), (u'\u0bbe',u'\u0bc2'), (u'\u0bc6',u'\u0bc8'),
	(u'\u0bca',u'\u0bcd'), u'\u0bd7', (u'\u0c01',u'\u0c03'), (u'\u0c3e',u'\u0c44'),
	(u'\u0c46',u'\u0c48'), (u'\u0c4a',u'\u0c4d'), (u'\u0c55',u'\u0c56'),
	(u'\u0c82',u'\u0c83'), (u'\u0cbe',u'\u0cc4'), (u'\u0cc6',u'\u0cc8'),
	(u'\u0cca',u'\u0ccd'), (u'\u0cd5',u'\u0cd6'), (u'\u0d02',u'\u0d03'),
	(u'\u0d3e',u'\u0d43'), (u'\u0d46',u'\u0d48'), (u'\u0d4a',u'\u0d4d'), u'\u0d57',
	u'\u0e31', (u'\u0e34',u'\u0e3a'), (u'\u0e47',u'\u0e4e'), u'\u0eb1',
	(u'\u0eb4',u'\u0eb9'), (u'\u0ebb',u'\u0ebc'), (u'\u0ec8',u'\u0ecd'),
	(u'\u0f18',u'\u0f19'), u'\u0f35', u'\u0f37', u'\u0f39', (u'\u0f3e',u'\u0f3f'),
	(u'\u0f71',u'\u0f84'), (u'\u0f86',u'\u0f8b'), (u'\u0f90',u'\u0f95'), u'\u0f97',
	(u'\u0f99',u'\u0fad'), (u'\u0fb1',u'\u0fb7'), u'\u0fb9', (u'\u20d0',u'\u20dc'),
	u'\u20e1', (u'\u302a',u'\u302f'), (u'\u3099',u'\u309a'))

DigitClass=CharClass((u'0',u'9'), (u'\u0660',u'\u0669'),
	(u'\u06f0',u'\u06f9'), (u'\u0966',u'\u096f'), (u'\u09e6',u'\u09ef'),
	(u'\u0a66',u'\u0a6f'), (u'\u0ae6',u'\u0aef'), (u'\u0b66',u'\u0b6f'),
	(u'\u0be7',u'\u0bef'), (u'\u0c66',u'\u0c6f'), (u'\u0ce6',u'\u0cef'),
	(u'\u0d66',u'\u0d6f'), (u'\u0e50',u'\u0e59'), (u'\u0ed0',u'\u0ed9'),
	(u'\u0f20',u'\u0f29'))

ExtenderClass=CharClass(u'\xb7', (u'\u02d0',u'\u02d1'), u'\u0387', u'\u0640',
u'\u0e46', u'\u0ec6', u'\u3005', (u'\u3031',u'\u3035'), (u'\u309d',u'\u309e'),
(u'\u30fc',u'\u30fe'))

PubidCharClass=CharClass(u' ',u'\x0d',u'\x0a', (u'0',u'9'), (u'A',u'Z'), 
	(u'a',u'z'), "-'()+,./:=?;!*#@$_%")

def IsChar(c):
	return c and (ord(c)==0x9 or ord(c)==0xA or ord(c)==0xD or
		(ord(c)>=0x20 and ord(c)<=0xD7FF) or
		(ord(c)>=0xE000 and ord(c)<=0xFFFD) or
		(ord(c)>=0x10000 and ord(c)<=0x10FFFF))

def EscapeCharData(src,quote=False):
	"""Returns a unicode string with XML reserved characters escaped.
	
	We also escape return characters to prevent them being ignored.  If quote
	is True then the string is returned as a quoted attribute value."""
	if quote:
		return saxutils.quoteattr(src,{'\r':'&#xD;'})
	else:
		return saxutils.escape(src,{'\r':'&#xD;'})

def EscapeCDSect(src):
	"""Returns a unicode string enclosed in <!CDATA[[ ]]> with ]]> 
	by the clumsy sequence: ]]>]]&gt;<!CDATA[[
	
	Degenerate case: an empty string is returned as an empty string
	"""
	data=src.split(u']]>')
	if data:
		result=[u'<!CDATA[[',data[0]]
		for d in data[1:]:
			result.append(u']]>]]&gt;<!CDATA[[')
			result.append(d)
		result.append(u']]>')
		return string.join(result,u'')
	else:
		return u''
		
def EscapeCharData7(src,quote=False):
	"""Returns a unicode string with reserved and non-ASCII characters escaped."""
	dst=[]
	if quote:
		if "'" in src:
			q='"';qStr='&#x22'
		elif '"' in src:
			q="'";qStr='&#x27'
		else:
			q='"';qStr='&#x22'
		dst.append(q)
	else:
		q=None;qStr=''
	for c in src:
		if ord(c)>0x7F:
			if ord(c)>0xFF:
				if ord(c)>0xFFFF:
					if ord(c)>0xFFFFFF:
						dst.append("&#x%08X;"%ord(c))
					else:
						dst.append("&#x%06X;"%ord(c))
				else:
						dst.append("&#x%04X;"%ord(c))
			else:
					dst.append("&#x%02X;"%ord(c))
		elif c=='<':
			dst.append("&lt;")
		elif c=='&':
			dst.append("&amp;")
		elif c=='>':
			dst.append("&gt;")
		elif c=='\r':
			dst.append("&#xD;")
		elif c==q:
			dst.append(qStr)
		else:
			dst.append(c)
	if quote:
		dst.append(q)	
	return string.join(dst,'')
	

def IsS(c):
	return c and (ord(c)==0x9 or ord(c)==0xA or ord(c)==0xD or ord(c)==0x20)

def CollapseSpace(data,sMode=True,sTest=IsS):
	"""Returns data with all spaces collapsed to a single space.
	
	sMode determines the fate of any leading space, by default it is True and
	leading spaces are ignored provided the string has some non-space
	characters.

	You can override the test of what consitutes a space by passing a function
	for sTest, by default we use IsS.

	Note on degenerate case: this function is intended to be called with
	non-empty strings and will never *return* an empty string.  If there is no
	data then a single space is returned (regardless of sMode)."""
	result=[]
	for c in data:
		if sTest(c):
			if not sMode:
				result.append(u' ')
			sMode=True
		else:
			sMode=False
			result.append(c)
	if result:
		return string.join(result,'')
	else:
		return ' '

def IsLetter(c):
	return IsBaseChar(c) or IsIdeographic(c)

def IsBaseChar(c):
	return BaseCharClass.Test(c)

def IsIdeographic(c):
	return c and ((ord(c)>=0x4E00 and ord(c)<=0x9FA5) or ord(c)==0x3007 or
		(ord(c)>=0x3021 and ord(c)<=0x3029))

def IsCombiningChar(c):
	return CombiningCharClass.Test(c)

def IsDigit(c):
	return DigitClass.Test(c)

def IsExtender(c):
	return ExtenderClass.Test(c)

def IsNameStartChar(c):
	return NameStartCharClass.Test(c)
	
def IsNameChar(c):
	return NameCharClass.Test(c)

def IsValidName(name):
	if name:
		if not IsNameStartChar(name[0]):
			return False
		for c in name[1:]:
			if not IsNameChar(c):
				return False
		return True
	else:
		return False

def IsPubidChar(c):
	return PubidCharClass.Test(c)


# def NormPath(urlPath):
# 	"""Normalizes a URL path, removing '.' and '..' components.
# 	
# 	An empty string (which tends to be a relative URL matching the current URL
# 	exactly) is returned unchanged.  The string "./" is also returned unchanged
# 	to avoid confusion with the empty string."""
# 	components=urlPath.split('/')
# 	pos=0
# 	while pos<len(components):
# 		if components[pos]=='.':
# 			# We can always remove '.', though "./" will need fixing later
# 			del components[pos]
# 		elif components[pos]=='':
# 			if pos>0 and pos<len(components)-1:
# 				# Remove "//"
# 				del components[pos]
# 			else:
# 				pos=pos+1
# 		elif components[pos]=='..':
# 			if pos>0 and components[pos-1] and components[pos-1]!='..':
# 				# remove "dir/.."
# 				del components[pos-1:pos+1]
# 				pos=pos-1
# 			else:
# 				pos=pos+1
# 		else:
# 			pos=pos+1
# 	if components==['']:
# 		return "./"
# 	else:
# 		return string.join(components,'/')

# def RelPath(basePath,urlPath,touchRoot=False):
# 	"""Return urlPath relative to basePath"""
# 	basePath=NormPath(basePath).split('/')
# 	urlPath=NormPath(urlPath).split('/')
# 	if basePath[0]:
# 		raise XMLURLPathError(string.join(basePath,'/'))
# 	if urlPath[0]:
# 		raise XMLURLPathError(string.join(urlPath,'/'))
# 	result=[]
# 	pos=1
# 	while pos<len(basePath):
# 		if result:
# 			if pos==2 and not touchRoot:
# 				result=['']+result
# 				break
# 			result=['..']+result
# 		else:
# 			if pos>=len(urlPath) or basePath[pos]!=urlPath[pos]:
# 				result=result+urlPath[pos:]
# 		pos=pos+1
# 	if not result and len(urlPath)>len(basePath):
# 		# full match but urlPath is longer
# 		return string.join(urlPath[len(basePath)-1:],'/')
# 	elif result==['']:
# 		return "./"
# 	else:
# 		return string.join(result,'/')		


def OptionalAppend(itemList,newItem):
	"""A convenience function which appends newItem to itemList if newItem is not None""" 
	if newItem is not None:
		itemList.append(newItem)


class XMLEntity:
	CHUNKSIZE=4096
	
	def __init__(self,src,encoding='utf-8'):
		self.encoding=encoding
		self.chunk=1
		if type(src) is UnicodeType:
			self.dataSource=None
			self.charSource=StringIO(src)
		elif isinstance(src,URI):
			if isinstance(src,FileURL):
				self.dataSource=open(src.GetPathname(),'rb')
				self.charSource=codecs.getreader(encoding)(self.dataSource)
			elif src.scheme.lower() in ['http','https']:
				reqManager=http.HTTPRequestManager()
				req=http.HTTPRequest(str(src))
				reqManager.ProcessRequest(req)
				if req.status==200:
					mtype=req.response.GetContentType()
					if mtype is None:
						# We'll attempt to do this with xml and utf8
						charset='utf8'
						raise UnimplementedError
					else:
						mimetype=mtype.type.lower()+'/'+mtype.subtype.lower()
						#if not self.ValidateXMLMimeType(mimetype):
						#	raise XMLContentTypeError(mimetype)
					self.dataSource=StringIO(req.resBody)
					self.charSource=codecs.getreader(encoding)(self.dataSource)
				else:
					raise XMLUnexpectedHTTPResponse(str(req.status))
			else:
				raise XMLUnsupportedScheme			
		else:
			if type(src) is StringType:
				self.dataSource=StringIO(src)
			else:
				self.dataSource=src
			self.charSource=codecs.getreader(encoding)(self.dataSource)
		self.basePos=self.charSource.tell()
		self.Reset()
		
	def Reset(self):
		self.charSource.seek(self.basePos)
		self.lineNum=1
		self.linePos=0
		self.chars=''
		self.charSeek=self.basePos
		self.charPos=-1
		self.theChar=''
		self.ignoreLF=False
		self.lookahead=[]
		self.NextChar()
		# python handles the utf-16 BOM automatically but we have to skip it for utf-8
		if self.encoding.lower()=='utf-8' and self.theChar==u'\ufeff':
			self.NextChar()
	
	def GetPositionStr(self):
		return "Line %i.%i"%(self.lineNum,self.linePos)
		
	def NextChar(self):
		"""Advance to the next character in the entity.
		
		This method takes care of the End-of-Line handling rules for XML which force
		us to remove any CR characters and replace them with LF if they appear on their
		own or silenty drop them if they appear as part of a CR-LF combination."""
		if self.theChar is None:
			return
		self.charPos=self.charPos+1
		self.linePos=self.linePos+1
		if self.charPos>=len(self.chars):
			# watch out for look ahead
			if self.lookahead:
				self.chars=self.chars+self.charSource.read(self.chunk)
			else:
				self.charSeek=self.charSource.tell()
				self.chars=self.charSource.read(self.chunk)
				self.charPos=0
		if self.charPos>=len(self.chars):
			self.theChar=None
		else:
			self.theChar=self.chars[self.charPos]
			if self.theChar=='\x0D':
				# change to a line feed and ignore the next line feed
				self.theChar='\x0A'
				self.ignoreLF=True
				self.NextLine()
			elif self.theChar=='\x0A':
				if self.ignoreLF:
					self.ignoreLF=False
					self.NextChar()
				else:
					self.NextLine()
			else:
				self.ignoreLF=False
				
	def ChangeEncoding(self,encoding):
		if self.dataSource:
			# Need to rewind and re-read the current buffer
			self.charSource.seek(self.charSeek)
			self.charSource=codecs.getreader(encoding)(self.dataSource)
			self.chars=self.charSource.read(len(self.chars))
			# We assume that charPos will still point to the correct next character
			self.theChar=self.chars[self.charPos]
			
	def NextLine(self):
		self.lineNum=self.lineNum+1
		self.linePos=0

	def StartLookahead(self):
		self.lookahead.append([self.lineNum,self.linePos,self.charPos,self.theChar,self.ignoreLF])
		
	def StopLookahead(self):
		self.lookahead.pop()
		
	def RewindLookahead(self):
		self.lineNum,self.linePos,self.charPos,self.theChar,self.ignoreLF=self.lookahead.pop()
		

class XMLParser:
	def __init__(self,entity=None):
		self.entity=entity
		self.entityStack=[]
		if self.entity:
			self.theChar=self.entity.theChar
		else:
			self.theChar=None
		self.buff=[]
		self.doc=None
		self.compatibilityMode=False
		
	def NextChar(self):
		"""Move to the next character in the stream."""
		if self.buff:
			self.buff=self.buff[1:]
		if self.buff:
			self.theChar=self.buff[0]
		else:	
			self.entity.NextChar()
			self.theChar=self.entity.theChar
			while self.theChar is None and self.entityStack:
				self.entity=self.entityStack.pop()
				self.theChar=self.entity.theChar

	def BuffText(self,unusedChars):
		if unusedChars:
			if self.buff:
				self.buff=list(unusedChars)+self.buff
			else:
				self.buff=list(unusedChars)
				if self.entity.theChar is not None:
					self.buff.append(self.entity.theChar)
			self.theChar=self.buff[0]
	
	def PushEntity(self,entity):
		"""Pushes a new entity onto the stack and starts parsing it."""
		self.entityStack.append(self.entity)
		self.entity=entity
		self.theChar=self.entity.theChar
	
	def WellFormednessViolation(self,msg="well-formedness violation"):
		raise XMLWellFormedError("%s: %s"%(self.entity.GetPositionStr(),msg))
		
	def ParseDocument(self,doc):
		"""[1] document ::= prolog element Misc* """
		self.doc=doc
		self.ParseProlog()
		self.ParseElement()
		self.ParseMisc()
		if self.theChar is not None:
			self.WellFormednessViolation("Unparsed characters in entity after document")

	#	[2] Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]

	def ParseS(self):
		""" [3] S ::= (#x20 | #x9 | #xD | #xA)+ """
		s=[]
		sLen=0
		while True:
			if IsS(self.theChar):
				s.append(self.theChar)
				self.NextChar()
			else:
				break
			sLen+=1
		return string.join(s,'')

	def ParseName(self):
		"""
		[4]		NameStartChar ::= ":" | [A-Z] | "_" | [a-z] | [#xC0-#xD6] | [#xD8-#xF6] | [#xF8-#x2FF] | [#x370-#x37D] | [#x37F-#x1FFF] | [#x200C-#x200D] | [#x2070-#x218F] | [#x2C00-#x2FEF] | [#x3001-#xD7FF] | [#xF900-#xFDCF] | [#xFDF0-#xFFFD] | [#x10000-#xEFFFF]
		[4a]   	NameChar ::= NameStartChar | "-" | "." | [0-9] | #xB7 | [#x0300-#x036F] | [#x203F-#x2040]
		[5]   	Name ::= NameStartChar (NameChar)*	"""
		name=[]
		if IsNameStartChar(self.theChar):
			name.append(self.theChar)
			self.NextChar()
			while IsNameChar(self.theChar):
				name.append(self.theChar)
				self.NextChar()
		if name:
			return string.join(name,'')
		else:
			return None

	def ParseRequiredName(self):
		name=self.ParseName()
		if name is None:
			self.WellFormednessViolation("Expected Name")
		return name
		
	def ParseNames(self):
		""" [6] Names ::= Name (#x20 Name)* """
		names=[]
		name=self.ParseName()
		if name is None:
			return None
		names.append(name)
		while self.theChar==u' ':
			self.NextChar()
			name=self.ParseName()
			if name is None:
				self.BuffText(u' ')
				break
			names.append(name)
		if names:
			return names
		else:
			return None
	
	def ParseNmtoken(self):
		"""[7] Nmtoken ::= (NameChar)+ """
		nmtoken=[]
		while IsNameChar(self.theChar):
			nmtoken.append(self.theChar)
			self.NextChar()
		if nmtoken:
			return string.join(nmtoken,'')
		else:
			return None

	def ParseNmtokens(self):
		""" [8] Nmtokens ::= Nmtoken (#x20 Nmtoken)* """
		nmtokens=[]
		nmtoken=self.ParseNmtoken()
		if nmtoken is None:
			return None
		nmtokens.append(nmtoken)
		while self.theChar==u' ':
			self.NextChar()
			nmtoken=self.ParseNmtoken()
			if nmtoken is None:
				self.BuffText(u' ')
				break
			nmtokens.append(nmtoken)
		if nmtokens:
			return nmtokens
		else:
			return None
	
	def ParseEntityValue(self):
		"""[9] EntityValue ::= '"' ([^%&"] | PEReference | Reference)* '"' | "'" ([^%&'] | PEReference | Reference)* "'"	"""
		q=self.ParseQuote()
		value=[]
		while True:
			if self.theChar=='&':
				value.append(self.ParseReference())
			elif self.theChar=='%':
				self.ParsePEReference()
			elif self.theChar==q:
				self.NextChar()
				break
			elif IsChar(self.theChar):
				value.append(self.theChar)
				self.NextChar()
			elif self.theChar is None:
				self.WellFormednessViolation("Incomplete EntityValue")
			else:
				self.WellFormednessViolation("Unexpected data in EntityValue")
		return string.join(value,'')

	def ParseAttValue(self):
		"""[10] AttValue ::= '"' ([^<&"] | Reference)* '"' |  "'" ([^<&'] | Reference)* "'" """
		value=[]
		try:
			q=self.ParseQuote()
			end=''
		except XMLWellFormedError:
			if not self.compatibilityMode:
				raise
			q=None
			end='<"\'> \t\r\n'
		while True:
			try:
				if self.theChar==q:
					self.NextChar()
					break
				elif self.theChar in end:
					# compatibility mode only
					break
				elif self.theChar=='&':
					refData=self.ParseReference()
					value.append(refData)
				elif IsS(self.theChar):
					value.append(unichr(0x20))
					self.NextChar()
				elif self.theChar=='<':
					self.WellFormednessViolation("Unescaped < in AttValue")
				elif self.theChar is None:
					self.WellFormednessViolation("EOF in AttValue")
				else:
					value.append(self.theChar)
					self.NextChar()
			except XMLWellFormedError:
				if not self.compatibilityMode:
					raise
				elif self.theChar=='<':
					value.append(self.theChar)
					self.NextChar()
				elif self.theChar is None:
					break
		return string.join(value,'')
	
	def ParseSystemLiteral(self):
		"""[11] SystemLiteral ::= ('"' [^"]* '"') | ("'" [^']* "'") """
		q=self.ParseQuote()
		value=[]
		while True:
			if self.theChar==q:
				self.NextChar()
				break
			elif IsChar(self.theChar):
				value.append(self.theChar)
				self.NextChar()
			elif self.theChar is None:
				self.WellFormednessViolation("Incomplete SystemLiteral")
			else:
				self.WellFormednessViolation("Unexpected data in SystemLiteral")
		return string.join(value,'')
		
	def ParsePubidLiteral(self):
		"""
		[12] PubidLiteral ::= '"' PubidChar* '"' | "'" (PubidChar - "'")* "'"
		[13] PubidChar ::= #x20 | #xD | #xA | [a-zA-Z0-9] | [-'()+,./:=?;!*#@$_%]
		"""
		q=self.ParseQuote()
		value=[]
		while True:
			if self.theChar==q:
				self.NextChar()
				break
			elif IsPubidChar(self.theChar):
				value.append(self.theChar)
				self.NextChar()
			elif self.theChar is None:
				self.WellFormednessViolation("Incomplete PubidLiteral")
			else:
				self.WellFormednessViolation("Unexpected data in PubidLiteral")
		return string.join(value,'')

	def ParseCharData(self):
		"""[14] CharData ::= [^<&]* - ([^<&]* ']]>' [^<&]*) """
		data=[]
		while self.theChar is not None:
			if self.theChar=='<' or self.theChar=='&':
				break
			if self.theChar==']':
				match=self.ParseLiteral(']]>')
				if match:
					break
			data.append(self.theChar)
			self.NextChar()
		return string.join(data,'')					

	def ParseComment(self):
		"""[15] Comment ::= '<!--' ((Char - '-') | ('-' (Char - '-')))* '-->'
		
		Assume the literal has already been parsed."""
		data=[]
		while self.theChar is not None:
			if self.theChar=='-':
				self.NextChar()
				if self.theChar=='-':
					# must be the end of the comment
					self.NextChar()
					if self.theChar=='>':
						self.NextChar()
						break
					else:					
						raise XMLCommentError
				else:
					# just a single '-'
					data.append('-')
			data.append(self.theChar)
			self.NextChar()
		return string.join(data,'')

	def ParsePI(self):
		"""
		[16] PI ::= '<?' PITarget (S (Char* - (Char* '?>' Char*)))? '?>'
		[17] PITarget ::= Name - (('X' | 'x') ('M' | 'm') ('L' | 'l'))
		
		Assume the literal has already been parsed.
		"""
		data=[]
		target=self.ParseName()
		if target is None:
			self.WellFormednessViolation("Expected PI Target")
		if self.ParseS() is None:
			return target,None
		while self.theChar is not None:
			if self.theChar=='?':
				self.NextChar()
				if self.theChar=='>':
					self.NextChar()
					break
				else:
					# just a single '?'
					data.append('?')
			data.append(self.theChar)
			self.NextChar()
		return target,string.join(data,'')
		
	def ParseCDSect(self,cdEnd=u']]>'):
		"""
		[18] CDSect ::= CDStart CData CDEnd
		[19] CDStart ::= '<![CDATA['
		[20] CData ::= (Char* - (Char* ']]>' Char*))
		[21] CDEnd ::= ']]>'
		
		Assume that the initial literal has already been parsed."""
		data=[]
		while self.theChar is not None:
			if self.ParseLiteral(cdEnd):
				break
			data.append(self.theChar)
			self.NextChar()
		return string.join(data,'')

	def ParseProlog(self):
		"""[22] prolog ::= XMLDecl? Misc* (doctypedecl Misc*)?"""
		match=self.ParseLiteral('<?xml')
		if match:
			self.ParseXMLDecl()
		self.entity.chunk=XMLEntity.CHUNKSIZE
		self.ParseMisc()
		match=self.ParseLiteral('<!DOCTYPE')
		if match:
			self.ParseDoctypeDecl()
			self.ParseMisc()
		return None
		
	def ParseXMLDecl(self):
		"""Returns the XML declaration information: version, encoding, standalone.
		
		The initial literal is assumed to have already been parsed.
		
		[23] XMLDecl ::= '<?xml' VersionInfo EncodingDecl? SDDecl? S? '?>'
		[24] VersionInfo ::= S 'version' Eq ("'" VersionNum "'" | '"' VersionNum '"')
		[26] VersionNum ::= '1.' [0-9]+
		"""
		encoding=None
		standalone=None
		self.ParseS()
		self.ParseRequiredLiteral(u'version')
		self.ParseEq()
		q=self.ParseQuote()
		self.ParseRequiredLiteral(u'1.')
		digits=self.ParseDecimalDigits(True)
		version="1."+digits
		self.ParseQuote(q)
		s=self.ParseS()
		if s:
			match=self.ParseLiteral('encoding')
			if match:
				encoding=self.ParseEncodingDecl()
				s=self.ParseS()
		if s:
			match=self.ParseLiteral('standalone')
			if match:
				standalone=self.ParseSDDecl()
				s=self.ParseS()
		self.ParseRequiredLiteral('?>')
		if encoding and self.entity.encoding.lower()!=encoding.lower():
			self.entity.ChangeEncoding(encoding)
		return version,encoding,standalone
	
	def ParseEq(self):
		"""[25] Eq ::= S? '=' S? """
		self.ParseS()
		self.ParseRequiredLiteral(u'=')
		self.ParseS()
		
	def ParseMisc(self):
		"""[27] Misc ::= Comment | PI | S
		This method returns and trailing data matching S; that is, any data
		after all comments and processing instructions have been parsed."""
		s=[]
		while True:
			match=self.ParseLiteral('<!--')
			if match:
				s=[]
				self.ParseComment()
				continue
			match=self.ParseLiteral('<?')
			if match:
				s=[]
				self.ParsePI()
				continue
			match=self.ParseS()
			if not match:
				break
			else:
				s.append(match)
		return string.join(s,'')
		
	def ParseDoctypeDecl(self):
		"""
		[28]  doctypedecl ::= '<!DOCTYPE' S Name (S ExternalID)? S? ('[' intSubset ']' S?)? '>'
		[28a] DeclSep ::= PEReference | S	[WFC: PE Between Declarations]
		[28b] intSubset ::= (markupdecl | DeclSep)*
		[29]  markupdecl ::= elementdecl | AttlistDecl | EntityDecl | NotationDecl | PI | Comment
		Assume the literal has already been parsed."""
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		dtdName=self.ParseRequiredName()
		s=self.ParseS()
		if s:
			if self.theChar=='S' or self.theChar=='P':
				pubID,systemID=self.ParseExternalID()
				self.ParseS()
		if self.theChar=='[':
			#import pdb;pdb.set_trace()
			self.NextChar()
			while True:
				if self.theChar=='%':
					self.ParsePEReference()
				elif self.theChar==']':
					self.NextChar()
					break
				elif self.theChar=='<':
					# markupdecl of some sort
					self.NextChar()
					if self.theChar=='?':
						self.NextChar()
						self.ParsePI()
					elif self.theChar=='!':
						self.NextChar()
						if self.theChar=='-':
							self.ParseRequiredLiteral('--')
							self.ParseComment()
						elif self.ParseLiteral('ELEMENT'):
							self.ParseElementDecl()
						elif self.ParseLiteral('ATTLIST'):
							self.ParseAttlistDecl()
						elif self.ParseLiteral('ENTITY'):
							self.PasreEntityDecl()
						elif self.ParseLiteral('NOTATION'):
							self.ParseNotationDecl()
					else:
						self.WellFormednessViolation("Expected markupdecl")
				elif not self.ParseS():
					self.WellFormednessViolation("Expected markupdecl or DeclSep")
			self.ParseS()
		self.ParseRequiredLiteral('>')
		return None
		
	def ParseSDDecl(self):
		"""[32] SDDecl ::= S 'standalone' Eq (("'" ('yes' | 'no') "'") | ('"' ('yes' | 'no') '"')) 
		
		Assume that the 'standalone' literal has already been parsed."""
		self.ParseEq()
		q=self.ParseQuote()
		if self.theChar==u'y':
			result=True
			match=u'yes'
		else:
			result=False
			match=u'no'
		self.ParseRequiredLiteral(match)
		self.ParseQuote(q)
		return result
		
	STag=40
	ETag=42
	EmptyElemTag=44

	def ParseElement(self):
		"""[39] element ::= EmptyElemTag | STag content ETag"""
		name,attrs,empty=self.ParseSTag()
		if empty:
			self.doc.startElement(name,attrs)
			self.doc.endElement(name)
		else:
			self.doc.startElement(name,attrs)
			self.ParseContent()
			endName=self.ParseETag()
			if name!=endName:
				self.WellFormednessViolation("Expected <%s/>"%name)
			self.doc.endElement(name)
		return name
	
	def ParseSTag(self):
		"""To avoid needless lookahead we combine parsing of EmptyElemTag into this method.
		
		[40] STag ::= '<' Name (S Attribute)* S? '>'
		[44] EmptyElemTag ::= '<' Name (S Attribute)* S? '/>'
		"""
		empty=False
		self.ParseRequiredLiteral('<')
		name=self.ParseName()
		if name is None:
			self.WellFormednessViolation("Expected Name")
		attrs={}
		while True:
			try:
				s=self.ParseS()
				if self.theChar=='>':
					self.NextChar()
					break
				elif self.theChar=='/':
					self.ParseRequiredLiteral('/>')
					empty=True
					break
				if s:
					aName,aValue=self.ParseAttribute()
					attrs[aName]=aValue
				else:
					#import pdb;pdb.set_trace()
					self.WellFormednessViolation("Expected S, '>' or '/>', found '%s'"%self.theChar)
			except XMLWellFormedError:
				if not self.compatibilityMode:
					raise
				# spurious character inside a start tag, in compatibility mode we
				# just discard it and keep going
				self.NextChar()
				continue
		return name,attrs,empty
	
	def ParseETag(self):
		"""[42] ETag ::= '</' Name S? '>' """
		self.ParseRequiredLiteral('</')
		name=self.ParseName()
		if name is None:
			self.WellFormednessViolation("Expected Name")
		self.ParseS()
		self.ParseRequiredLiteral('>')
		return name
		
	def ParseContent(self):
		"""[43] content ::= CharData? ((element | Reference | CDSect | PI | Comment) CharData?)* """
		while True:
			if self.theChar=='<':
				self.NextChar()
				if self.theChar=='!':
					self.NextChar()
					if self.theChar=='-':
						self.ParseRequiredLiteral('--')
						self.ParseComment()
					elif self.theChar=='[':
						self.ParseRequiredLiteral('[CDATA[')
						data=self.ParseCDSect()
						if data:
							self.doc.characters(data)
					else:
						self.WellFormednessViolation("Expected Comment or CDSect")
				elif self.theChar=='?':
					self.NextChar()
					self.ParsePI()
				elif self.theChar!='/':
					self.BuffText('<')
					self.ParseElement()
				else:
					self.BuffText('<')
					break
			elif self.theChar=='&':
				data=self.ParseReference()
				if data:
					self.doc.characters(data)
			elif self.theChar is None:
				self.WellFormednessViolation("Unexpected end of content")
			else:
				data=self.ParseCharData()
				if data:
					self.doc.characters(data)
				else:
					self.WellFormednessViolation("Unrecognized character in content: %s"%self.theChar)
	
	def ParseElementDecl(self):
		"""[45] elementdecl ::= '<!ELEMENT' S Name S contentspec S? '>'
		Assume that the literal has already been parsed."""
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		name=self.ParseName()
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		self.ParseContentSpec()
		self.ParseS()
		self.ParseRequiredLiteral('>')
	
	def ParseContentSpec(self):
		"""
		[46] contentspec ::= 'EMPTY' | 'ANY' | Mixed | children
		[47] children	::=   	(choice | seq) ('?' | '*' | '+')?
		[51] Mixed 		::=   	'(' S? '#PCDATA' (S? '|' S? Name)* S? ')*' | '(' S? '#PCDATA' S? ')'
		"""
		if self.ParseLiteral('EMPTY'):
			return
		elif self.ParseLiteral('ANY'):
			return
		else:
			self.ParseRequiredLiteral('(')
			self.ParseS()
			if self.ParseLiteral('#PCDATA'):
				# Mixed
				while True:
					self.ParseS()
					if self.theChar==')':
						self.NextChar()
						break
					elif self.theChar=='|':
						self.NextChar()
						self.ParseS()
						self.ParseName()
					else:
						self.WellFormednessViolation("Expected Name, '|' or ')'")
				if self.theChar=='*':
					self.NextChar()
			else:
				self.ParseChoiceOrSeq()
				if self.theChar in '?*+':
					self.NextChar()

	def ParseChoiceOrSeq(self):
		"""
		[48] cp			::=   	(Name | choice | seq) ('?' | '*' | '+')?
		[49] choice		::=   	'(' S? cp ( S? '|' S? cp )+ S? ')'
		[50] seq		::=   	'(' S? cp ( S? ',' S? cp )* S? ')'
		
		Assume we already have the '(' and any S
		"""
		sep=None
		while True:
			if self.theChar=='(':
				self.NextChar()
				self.ParseS()
				self.ParseChoiceOrSeq()
			else:
				self.ParseName()
			if self.theChar in '?*+':
				self.NextChar()
			self.ParseS()
			if sep is None:
				if self.theChar=='|':
					sep='|'
				elif self.theChar==',':
					sep=','
				elif self.theChar==')':
					self.NextChar()
					break
				self.NextChar()
			elif self.theChar==sep:
				self.NextChar()
			elif self.theChar==')':
				self.NextChar()
				break
			else:
				self.WellFormednessViolation("Bad separator in content group %s"%self.theChar)
			self.ParseS()

	def ParseAttlistDecl(self):
		"""
		[52] AttlistDecl	::= '<!ATTLIST' S Name AttDef* S? '>'
		[53] AttDef			::= S Name S AttType S DefaultDecl
		Assume that the literal has already been parsed."""
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		eName=self.ParseName()
		while True:
			if not self.ParseS() or self.theChar==">":
				break
			aName=self.ParseName()
			if not self.ParseS():
				self.WellFormednessViolation("Expected S")
			aType=self.ParseAttType()
			if not self.ParseS():
				self.WellFormednessViolation("Expected S")
			aDefaultType,aDefaultValue=self.ParseDefaultDecl()
		self.ParseRequiredLiteral('>')
	
	def ParseAttType(self):
		"""
		[54] AttType		::= StringType | TokenizedType | EnumeratedType
		[55] StringType 	::= 'CDATA'
		[56] TokenizedType	::= 'ID' | 'IDREF' | 'IDREFS' | 'ENTITY' | 'ENTITIES' | 'NMTOKEN' | 'NMTOKENS'
		[57] EnumeratedType ::= NotationType | Enumeration
		[58] NotationType	::= 'NOTATION' S '(' S? Name (S? '|' S? Name)* S? ')'
		[59] Enumeration	::= '(' S? Nmtoken (S? '|' S? Nmtoken)* S? ')'
		"""
		if self.theChar=="(":
			# An Enumeration
			self.NextChar()
			enumeration=[]
			while True:
				self.ParseS()
				enumeration.append(self.ParseNmtoken())
				self.ParseS()
				if self.theChar=='|':
					self.NextChar()
					continue
				elif self.theChar==')':
					self.NextChar()
					break
				else:
					self.WellFormednessViolation("Expected '|' or ')' in Enumeration")
			return ['']+enumeration
		else:
			type=self.ParseName()
			if type=="NOTATION":
				if not self.ParseS():
					self.WellFormednessViolation("Expected S")
				self.ParseRequiredLiteral('(')
				notation=[]
				while True:
					self.ParseS()
					notation.append(self.ParseName())
					self.ParseS()
					if self.theChar=='|':
						self.NextChar()
						continue
					elif self.theChar==')':
						self.NextChar()
						break
					else:
						self.WellFormednessViolation("Expected '|' or ')' in NotationType")
				return [type]+notation
			else:
				return [type]
	
	def ParseDefaultDecl(self):
		"""[60] DefaultDecl	::=	'#REQUIRED' | '#IMPLIED' | (('#FIXED' S)? AttValue)"""
		if self.ParseLiteral('#REQUIRED'):
			return '#REQUIRED',''
		elif self.ParseLiteral('#IMPLIED'):
			return '#IMPLIED',''
		else:
			if self.ParseLiteral('#FIXED'):
				type="#FIXED"
				if not self.ParseS():
					self.WellFormednessViolation("Expected S")
			else:
				type=''
			value=self.ParseAttValue()
			return type,value
			
	def ParsePEReference(self):
		"""[69] PEReference ::= '%' Name ';'  """
		self.ParseRequiredLiteral('%')
		name=self.ParseName()
		self.ParseRequiredLiteral(';')
		e=self.LookupParameterEntity(name)
		if e is not None:
			# Parameter entities are fed back into the parser somehow
			self.PushEntity(e)
	
	def ParseExternalID(self):
		"""[75] ExternalID ::= 'SYSTEM' S SystemLiteral | 'PUBLIC' S PubidLiteral S SystemLiteral """
		if self.ParseLiteral('SYSTEM'):
			pubID=None
		elif self.ParseLiteral('PUBLIC'):
			if not self.ParseS():
				self.WellFormednessViolation("Expected S")
			pubID=self.ParsePubidLiteral()
		else:
			self.WellFormednessViolation("Expected ExternalID")
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		systemID=self.ParseSystemLiteral()
		return pubID,systemID
			
	def ParseEncodingDecl(self):
		"""[80] EncodingDecl ::= S 'encoding' Eq ('"' EncName '"' | "'" EncName "'" )
		
		We assume that the 'encoding' literal has already been parsed."""
		self.ParseEq()
		q=self.ParseQuote()
		encName=self.ParseEncName()
		if not encName:
			self.WellFormednessViolation("Expected EncName")
		self.ParseQuote(q)
		return encName
		
	def ParseEncName(self):
		"""[81] EncName ::= [A-Za-z] ([A-Za-z0-9._] | '-')* """
		name=[]
		if EncNameStartCharClass.Test(self.theChar):
			name.append(self.theChar)
			self.NextChar()
			while EncNameCharClass.Test(self.theChar):
				name.append(self.theChar)
				self.NextChar()
		if name:
			return string.join(name,'')
		else:
			return None
			
	def ParseNotationDecl(self):
		"""[82] NotationDecl ::= '<!NOTATION' S Name S (ExternalID | PublicID) S? '>'
		
		We assume that <!NOTATION has already been parsed."""
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		name=self.ParseName()
		if name is None:
			self.WellFormednessViolation("Expected NOTATION Name")
		if not self.ParseS():
			self.WellFormednessViolation("Expected S")
		if self.theChar=='S':
			# Must be a SYSTEM literal in an ExternalID
			pubID,systemID=self.ParseExternalID()
		elif self.ParseLiteral('PUBLIC'):
			if not self.ParseS():
				self.WellFormednessViolation("Expected S")
			pubID=self.ParsePubidLiteral()
			systemID=None
			if self.ParseS():
				# Could also have a SYSTEM ID
				if self.ParseLiteral('SYSTEM'):
					systemID=self.ParseSystemLiteral()
				self.ParseS()
		else:
			self.WellFormednessViolation("Expected ExternalID or PublicID")
		self.ParseRequiredLiteral('>')
		return pubID,systemID
			

	def ParseAttribute(self):
		"""Return name, value
		
		We are very generous in our parsing of these values to accommodate common
		failings such as missing or unquoted values for attributes."""
		name=self.ParseName()
		self.ParseS()
		if self.ParseLiteral('='):
			self.ParseS()
			value=self.ParseAttValue()
		else:
			value=name
		return name,value
	
	stdEntities={
		'lt':'<',
		'gt':'>',
		'apos':"'",
		'quot':'"',
		'amp':'&'}
		
	def ParseReference(self):
		if self.theChar=='&':
			self.NextChar()
			if self.theChar=='#':
				self.NextChar()
				if self.theChar=='x':
					self.NextChar()
					data=unichr(int(self.ParseHexDigits(),16))
				else:
					data=unichr(int(self.ParseDecimalDigits()))
			else:
				name=self.ParseName()
				data=XMLParser.stdEntities.get(name,None)
				if data is None:
					data=self.LookupEntity(name)
			self.ParseLiteral(';')
		return data
	
	def LookupEntity(self,name):
		return ''
	
	def LookupParameterEntity(self,name):
		if self.doc:
			e=self.doc.GetParameterEntity(name)
		else:
			e=None
		return e

	def ParseDecimalDigits(self,required=False):
		data=[]
		while self.theChar in "0123456789":
			data.append(self.theChar)
			self.NextChar()
		if required and not data:
			self.WellFormednessViolation("Expected [0-9]+")
		return string.join(data,'')

	def ParseHexDigits(self):
		data=[]
		while self.theChar in "0123456789abcdefABCDEF":
			data.append(self.theChar)
			self.NextChar()
		return string.join(data,'')

	def ParseQuote(self,q=None):
		"""Parses the quote character, q, or one of "'" or '"' if q is None.
		
		Returns the character parsed or raises a well formed error."""
		if q:
			if self.theChar==q:
				self.NextChar()
				return q
			else:
				self.WellFormednessViolation("Expected %s"%q)
		elif self.theChar=='"' or self.theChar=="'":
			q=self.theChar
			self.NextChar()
			return q
		else:
			self.WellFormednessViolation("Expected '\"' or \"'\"")
					
	def ParseRequiredLiteral(self,match):
		"""Parses a required literal string raising a wellformed error if not matched """
		if not self.ParseLiteral(match):			
			self.WellFormednessViolation("Expected %s"%match)
			
	def ParseLiteral(self,match):
		"""Returns a Boolean if the literal was matched successfully"""
		matchLen=0
		for m in match:
			if m!=self.theChar:
				self.BuffText(match[:matchLen])
				break
			matchLen+=1
			self.NextChar()
		return matchLen==len(match)
			

class XMLElement:
	#XMLCONTENT=XMLMixedContent
	
	def __init__(self,parent,name=None):
		self.parent=parent
		if name is None:
			if hasattr(self.__class__,'XMLNAME'):
				self.xmlname=self.__class__.XMLNAME
			else:
				self.xmlname=None
		else:
			self.xmlname=name
		self.id=None
		self._attrs={}
		self._children=[]

	def SetXMLName(self,name):
		self.xmlname=name
	
	def GetXMLName(self):
		return self.xmlname
		
	def GetDocument(self):
		"""Returns the document that contains the element.
		
		If the element is an orphan, or is the descendent of an orphan
		then None is returned."""
		if self.parent:
			if isinstance(self.parent,XMLDocument):
				return self.parent
			else:
				return self.parent.GetDocument()
		else:
			return None

	def SetID(self,id):
		"""Sets the id of the element, registering the change with the enclosing document.
		
		If the id is already taken then XMLIDClashError is raised."""
		if not self.IsValidName(id):
			raise XMLIDValueError(id)
		doc=self.GetDocument()
		if doc:
			doc.UnregisterElement(self)
			self.id=id
			doc.RegisterElement(self)
		else:
			self.id=id
		
	def GetAttributes(self):
		"""Returns a dictionary object that maps attribute names onto values.
		
		Each attribute value is represented as a (possibly unicode) string.
		Derived classes should override this method if they define any custom
		attribute setters.
		
		The dictionary returned represents a copy of the information in the element
		and so may be modified by the caller."""
		attrs=copy(self._attrs)
		if self.id:
			attrs[self.__class__.ID]=self.id
		for a in dir(self.__class__):
			if a.startswith('XMLATTR_'):
				required=False
				setter=getattr(self.__class__,a)
				if type(setter) in StringTypes:
					# use simple attribute assignment
					name,encode=setter,lambda x:x
				elif type(setter) is TupleType:
					if len(setter)==3:
						name,decode,encode=setter
					elif len(setter)==4:
						name,decode,encode,required=setter
					else:
						raise XMLAttributeSetter("bad XMLATTR_ definition: %s attribute of %s"%(name,self.__class__.__name__))
				else:
					raise XMLAttributeSetter("setting %s attribute of %s"%(name,self.__class__.__name__))				
				value=getattr(self,name,None)
				if type(value) is ListType:
					value=string.join(map(encode,value),' ')
					if not value and not required:
						value=None
				elif type(value) is DictType:
					value=string.join(sorted(map(encode,value.keys())),' ')
					if not value and not required:
						value=None
				elif value is not None:
					value=encode(value)
				if value is not None:
					attrs[a[8:]]=value
		return attrs

	def SetAttribute(self,name,value):
		"""Sets the value of an attribute.
		
		The attribute name is assumed to be a string or unicode string.
		
		The default implementation checks for a custom setter which can be defined
		in one of three ways.
		
		(1) For simple assignement of the string value to an attribute of the
		instance just add an attribute to the class of the form
		XMLATTR_xmlname='member' where 'xmlname' is the attribute name used in
		the XML tag and 'member' is the attribute name to use in the instance.

		(2) More complex attributes can be handled by setting XMLATTR_xmlname to
		a tuple of ('member',decodeFunction,encodeFunction) where the
		decodeFunction is a simple function that take a string argument and
		returns the decoded value of the attribute, the encodeFunction performs
		the reverse transformation.
		
		In cases (1) and (2), once the member name has been determined the
		existing value of the member is used to determine how to set the value:
		
		List: split the value by whitespace and assign list of decoded values

		Dict: split the value by whitespace and create a mapping from decoded
		values to the original text used to represent it in the attribute.		

		Any other type: the member is set to the decoded value
		
		A values of None or a missing member is as treated as for 'any other type'.
		
		(3) Finally, if the *instance* has a method called Set_xmlname then that
		is called with the value.
		
		In the first two cases, GetAttributes will handle the generation of the
		attribute automatically, in the third case you must override the
		GetAttributes method to set the attributes appropriately during
		serialization back to XML.
		
		XML attribute names may contain many characters that are not legal in
		Python method names but, in practice, the only significant limitation is
		the colon.  This is replaced by '_' before searching for a custom setter.
		
		If no custom setter is defined then the default processing stores the
		attribute in a local dictionary, a copy of which can be obtained with
		the GetAttributes method.  Additionally, if the class has an ID
		attribute it is used as the name of the attribute that represents the
		element's ID.  ID handling is performed automatically at document level
		and the element's 'id' attribute is set accordingly."""
		setter=getattr(self,"XMLATTR_"+name,None)
		if setter is None:
			setter=getattr(self,"Set_"+name,None)
			if setter is None:
				if hasattr(self.__class__,'ID') and name==self.__class__.ID:
					self.SetID(value)
				else:
					self._attrs[name]=value
			else:
				setter(value)
		else:
			if type(setter) in StringTypes:
				# use simple attribute assignment
				name,decode=setter,lambda x:x
			elif type(setter) is TupleType:
				if len(setter)==3:
					name,decode,encode=setter
				else:
					# we ignore required when setting
					name,decode,encode,required=setter
			else:
				raise XMLAttributeSetter("setting %s attribute of %s"%(name,self.__class__.__name__))
			x=getattr(self,name,None)
			if type(x) is ListType:
				setattr(self,name,map(decode,value.split()))
			elif type(x) is DictType:
				value=value.split()
				setattr(self,name,dict(zip(map(decode,value),value)))
			else:
				setattr(self,name,decode(value))
	
	def IsValidName(self,value):
		return IsValidName(value)

	def IsEmpty(self):
		"""Returns True/False indicating whether this element *must* be empty.
		
		If the class defines the XMLCONTENT attribute then the model is taken
		from there and this method return True only if XMLCONTENT is XMLEmpty.
		
		Otherwise, the method defaults to False"""
		if hasattr(self.__class__,'XMLCONTENT'):
			return self.__class__.XMLCONTENT==XMLEmpty
		else:
			return False
		
	def IsMixed(self):
		"""Indicates whether or not the element *may* contain mixed content.
		
		If the class defines the XMLCONTENT attribute then the model is taken
		from there and this method return True only if XMLCONTENT is
		XMLMixedContent.
		
		Otherwise, the method default ot True"""
		if hasattr(self.__class__,'XMLCONTENT'):
			return self.__class__.XMLCONTENT==XMLMixedContent
		else:
			return True
		
	def GetChildren(self):
		"""Returns a list of the element's children.
		
		This method returns a copy of local list of children and so may be
		modified by the caller.  Derived classes with custom factory methods
		must override this method.

		Each child is either a string type, unicode string type or instance of
		XMLElement (or a derived class thereof)"""
		return copy(self._children)

	def GetCanonicalChildren(self):
		"""Returns a list of the element's children canonicalized for white space.
		
		We check the current setting of xml:space, returning the same list
		of children as GetChildren if 'preserve' is in force.  Otherwise we
		remove any leading space and collapse all others to a single space character."""
		children=self.GetChildren()
		if len(children)==0:
			return children
		e=self
		while isinstance(e,XMLElement):
			spc=e.GetSpace()
			if spc is not None:
				if spc=='preserve':
					return children
				else:
					break
			if hasattr(e.__class__,'SGMLCDATA'):
				return children
			e=e.parent
		if len(children)==1:
			child=children[0]
			if type(child) in StringTypes:
				children[0]=CollapseSpace(child)
				if len(children[0])>1 and children[0][-1]==' ':
					# strip the trailing space form the only child
					children[0]=children[0][:-1]				
		else:
			# Collapse strings to a single string entry and collapse spaces
			i=0
			while i<len(children):
				iChild=children[i]
				j=i
				while j<len(children):
					jChild=children[j]
					if type(jChild) in StringTypes:
						j=j+1
					else:
						break
				if j>i:
					# We need to collapse these children
					data=CollapseSpace(string.join(children[i:j],''),i==0)
					if i==0 and data==' ':
						# prune a leading space completely...
						del children[i:j]
					else:
						children[i:j]=[data]
				i=i+1
		if len(children)>1:
			if type(children[-1]) in StringTypes:
				if children[-1]==' ':
					# strip the whole last child
					del children[-1]
				elif children[-1][-1]==' ':
					# strip the trailing space form the last child
					children[-1]=children[-1][:-1]
		return children
		
	def _FindFactory(self,childClass):
		if hasattr(self,childClass.__name__):
			return childClass.__name__
		else:
			for parent in childClass.__bases__:
				fName=self._FindFactory(parent)
				if fName:
					return fName
			return None
				
	def ChildElement(self,childClass,name=None):
		"""Returns a new child of the given class attached to this element.
		
		A new child is created and attached to the element's model unless the
		model supports a single element of the given childClass and the element
		already exists, in which case the existing instance is returned.
		
		childClass is a class (or callable) used to create a new instance.
		
		name is the name given to the element (by the caller).  If no name is
		given then the default name for the child should be used.  When the
		child returned is an existing instance, name is ignored.
		
		The default implementation checks for a custom factory method and calls
		it if defined and does no further processing.  A custom factory method
		is a method of the form ClassName or an attribute that is being used to
		hold instances of this child.  The attribute must already exist and can
		be one of None (optional child, new child is created), a list (optional
		repeatable child, new child is created and appended) or an instance of
		childClass (required/existing child, no new child is created, existing
		instance returned).
		
		When no custom factory method is found the class hierarchy is also searched
		enabling generic members/methods to be used to hold similar objects.
		
		If no custom factory method is defined then the default processing
		simply creates an instance of child (if necessary) and attaches it to
		the local list of children."""
		if self.IsEmpty():
			self.ValidationError("Unexpected child element",name)
		factoryName=self._FindFactory(childClass)
		if factoryName:
			factory=getattr(self,factoryName)
			if type(factory) is MethodType:
				if factoryName!=childClass.__name__:
					child=factory(childClass)
				else:
					child=factory()
				if name:
					child.SetXMLName(name)
				return child
			elif type(factory) is NoneType:
				child=childClass(self)
				setattr(self,factoryName,child)
			elif type(factory) is ListType:
				child=childClass(self)
				factory.append(child)
			elif type(factory) is InstanceType and isinstance(factory,childClass):
				child=factory
			else:
				raise TypeError
		else:
			try:
				child=childClass(self)
			except TypeError:
				raise TypeError("Can't create %s in %s"%(childClass.__name__,self.__class__.__name__))
			self._children.append(child)
		if name:
			child.SetXMLName(name)
		return child
	
	def DeleteChild(self,child):
		"""Deletes the given child from this element's children.
		
		We follow the same factory conventions as for child creation except
		that an attribute pointing to a single child (or this class) will be
		replaced with None.  If a custom factory method is found then the
		corresponding Delete_ClassName method must also be defined.
		"""
		if self.IsEmpty():
			raise XMLUnknownChild(child.xmlname)
		factoryName=self._FindFactory(child.__class__)
		if factoryName:
			factory=getattr(self,factoryName)
			if type(factory) is MethodType:
				deleteFactory=getattr(self,"Delete_"+factoryName)
				deleteFactory(child)
			elif type(factory) is NoneType:
				raise XMLUnknownChild(child.xmlname)
			elif type(factory) is ListType:
				match=False
				for i in xrange(len(factory)):
					if factory[i] is child:
						child.DetachFromDocument()
						child.parent=None
						del factory[i]
						match=True
						break
				if not match:
					raise XMLUnknownChild(child.xmlname)
			elif factory is child:
				child.DetachFromDocument()
				child.parent=None
				factory=None
			else:
				raise TypeError
		else:
			match=False
			for i in xrange(len(self._children)):
				if self._children[i] is child:
					child.DetachFromDocument()
					child.parent=None
					del self._children[i]
					match=True
					break
			if not match:
				raise XMLUnknownChild(child.xmlname)
		
	def FindChildren(self,childClass,childList,max=None):
		"""Finds up to max children of class childClass from the element and
		its children.

		All matching children are added to childList.  If specifing a max number
		of matches then the incoming list must originally be empty to prevent
		early termination.

		Note that if max is None, the default, then all children of the given
		class are returned with the proviso that nested matches are not
		included.  In other words, if the model of childClass allows further
		elements of type childClass as children (directly or indirectly) then
		only the top-level match is returned.
		
		Effectively this method provides a breadth-first list of children.  For
		example, to get all <div> elements in an HTML <body> you would have to
		recurse over the resulting list calling FindChildren again until the
		list of matching children stops growing.		
		"""
		children=self.GetChildren()
		if max is not None and len(childList)>=max:
			return
		for child in children:
			if isinstance(child,childClass):
				childList.append(child)
			elif isinstance(child,XMLElement):
				child.FindChildren(childClass,childList,max)
			if max is not None and len(childList)>=max:
				break

	def FindParent(self,parentClass):
		"""Finds the first parent of class parentClass of this element.
		
		If this element has no parent of the given class then None is returned."""
		parent=self.parent
		while parent and not isinstance(parent,parentClass):
			if isinstance(parent,XMLElement):
				parent=parent.parent
			else:
				parent=None
		return parent
		
# 	def AdoptChild(self,child):
# 		"""Attaches an existing orphan child element to this one.
# 		
# 		The default implementation checks for a custom adoption method and
# 		calls it if defined and does no further processing.  A custom adoption
# 		method is a method of the form Adopt_ClassName.
# 		
# 		If a custom factory method is defined for the class of child but not a
# 		custom adoption method then TypeError is raised.  You are not required
# 		to provide a custom adoption method but you must do so if you wish to
# 		support the adoption of elements that would other require a custom
# 		factory to instantiate.
# 		
# 		If no custom adoption method or custom factory exists and the element is
# 		not empty then the child is added to the local list of children."""
# 		print "Adoption deprecated!"
# 		if child.parent:
# 			raise XMLParentError
# 		elif self.IsEmpty():
# 			self.ValidationError("Unexpected child element",child.xmlname)
# 		factory=getattr(self,child.__class__.__name__,None)
# 		adopter=getattr(self,"Adopt_"+child.__class__.__name__,None)
# 		if adopter is None:
# 			if factory:
# 				raise TypeError
# 			child.parent=self
# 			child.AttachToDocument()
# 			self._children.append(child)
# 		else:
# 			return adopter(child)
			
	def AttachToDocument(self,doc=None):
		"""Called when the element is first attached to a document.
		
		The default implementation ensures that any ID attributes belonging
		to this element or its descendents are registered."""
		if doc is None:
			doc=self.GetDocument()
		if doc:
			if self.id:
				doc.RegisterElement(self)
			for child in self.GetChildren():
				if isinstance(child,XMLElement):
					child.AttachToDocument(doc)
	
	def DetachFromDocument(self,doc=None):
		"""Called when an element is being detached from a document.
		
		The default implementation ensure that an ID attributes belonging
		to this element or its descendents are unregistered."""
		if doc is None:
			doc=self.GetDocument()
		if doc:
			if self.id:
				doc.UnregisterElement(self)
			for child in self.GetChildren():
				if isinstance(child,XMLElement):
					child.DetachFromDocument(doc)
		
	def AddData(self,data):
		"""Adds a string or unicode string to this element's children.
		
		If the element does not have mixed content then the data is ignored if
		it is white space, otherwise, ValidationError is called with the
		offending data."""
		assert(type(data) in StringTypes)
		if self.IsMixed():
			if self._children and type(self._children[-1]) in StringTypes:
				# To ease the comparison function we collapse string children
				self._children[-1]=self._children[-1]+data
			else:
				self._children.append(data)
		else:
			ws=True
			for c in data:
				if not IsS(c):
					ws=False
			if not ws:
				self.ValidationError("Unexpected data",data)

	def GotChildren(self):
		"""Notifies an element that all children have been added or created."""
		pass
	
	def GetValue(self,ignoreElements=False):
		"""Returns a single unicode string representing the element's data.
		
		If the element contains child elements and ignoreElements is False
		then XMLMixedContentError is raised.
		
		If the element is empty None is returned."""		
		children=self.GetChildren()
		if not ignoreElements:
			for child in children:
				if not type(child) in StringTypes:
					raise XMLMixedContentError(str(self))
		if children:
			return string.join(map(unicode,children),'')
		else:
			return None

	def SetValue(self,value):
		"""Replaces the value of the element with the (unicode) value.
		
		If the element has mixed content then XMLMixedContentError is
		raised."""
		if not self.IsMixed():
			raise XMLMixedContentError
		children=self.GetChildren()
		if len(children)!=len(self._children):
			raise XMLMixedContentError
		for child in children:
			if isinstance(child,XMLElement):
				child.DetachFromDocument()
				child.parent=None
		self._children=[unicode(value)]

	def ValidationError(self,msg,data=None,aname=None):
		"""Indicates that a validation error occurred in this element.
		
		An error message indicates the nature of the error.

		The data that caused the error may be given in data.
		
		Furthermore, the  attribute name may also be given indicating that the
		offending data was in an attribute of the element and not the element
		itself."""
		doc=self.GetDocument()
		if doc:
			doc.ValidationError(msg,self,data,aname)
		else:
			raise XMLValidationError(msg)
			

	def SortNames(self,nameList):
		"""Given a list of element or attribute names, sorts them in a predictable order
		
		The default implementation assumes that the names are strings or unicode strings
		so uses the default sort method."""
		nameList.sort()
		
	def __cmp__(self,element):
		"""Compares element with this one.
		
		XMLELement can only be compared with other XMLElements."""
		if not isinstance(element,XMLElement):
			raise TypeError
		#print "Comparing: <%s>, <%s>"%(str(self.xmlname),str(element.xmlname))
		result=cmp(self.xmlname,element.xmlname)
		if result:
			return result
		# sort and compare all attributes
		selfAttrs=self.GetAttributes()
		selfAttrNames=selfAttrs.keys()
		self.SortNames(selfAttrNames)
		elementAttrs=element.GetAttributes()
		elementAttrNames=elementAttrs.keys()
		element.SortNames(elementAttrNames)
		#print "Comparing attributes: \n%s\n...\n%s"%(str(selfAttrNames),str(elementAttrNames))
		for i in xrange(len(selfAttrNames)):
			if i>=len(elementAttrNames):
				# We're bigger by virtue of having more attributes!
				return 1
			selfAName=selfAttrNames[i]
			elementAName=elementAttrNames[i]
			result=cmp(selfAName,elementAName)
			if result:
				return result
			result=cmp(selfAttrs[selfAName],elementAttrs[selfAName])
			if result:
				return result
		if len(elementAttrNames)>len(selfAttrNames):
			# They're bigger by virtue of having more attributes!
			return -1
		selfChildren=self.GetCanonicalChildren()
		elementChildren=element.GetCanonicalChildren()
		for i in xrange(len(selfChildren)):
			if i>=len(elementChildren):
				# We're bigger by virtue of having more children
				return 1
			if isinstance(selfChildren[i],XMLElement):
				if isinstance(elementChildren[i],XMLElement):
					result=cmp(selfChildren[i],elementChildren[i])
				else:
					# elements sort before data
					result=-1
			elif isinstance(elementChildren[i],XMLElement):
				result=1
			else:
				# Data sorts by string comparison
				result=cmp(selfChildren[i],elementChildren[i])
			if result:
				return result
		if len(elementChildren)>len(selfChildren):
			return -1
		# Name, all attributes and child elements match!!
		return 0
	
	def __str__(self):
		"""Returns the XML element as a string.
		
		We force use of character references for all non-ascii characters in data
		but this isn't enough to guarantee success.  We will still get an encoding
		error if non-ascii characters have been used in markup names as such files
		cannot be encoded in US-ASCII."""
		s=StringIO()
		self.WriteXML(s,EscapeCharData7)
		return str(s.getvalue())
	
	def __unicode__(self):
		"""Returns the XML element as a unicode string"""
		s=StringIO()
		self.WriteXML(s,EscapeCharData)
		return unicode(s.getvalue())
		
	def Copy(self,parent=None):
		"""Creates a new instance of this element which is a deep copy of this one."""
		if parent:
			e=parent.ChildElement(self.__class__,self.GetXMLName())
		else:
			e=self.__class__(None)
		attrs=self.GetAttributes()
		for aname in attrs.keys():
			e.SetAttribute(aname,attrs[aname])
		children=self.GetChildren()
		for child in children:
			if type(child) in types.StringTypes:
				e.AddData(child)
			else:
				child.Copy(e)
		return e
		
	def GetBase(self):
		return self._attrs.get(xml_base,None)
	
	def SetBase(self,base):
		if base is None:
			self._attrs.pop(xml_base,None)
		else:
			self._attrs[xml_base]=str(base)

	def ResolveBase(self):
		"""Returns a fully specified URI for the base of the current element.
		
		The URI is calculated using any xml:base values of the element or its
		ancestors and ultimately relative to the baseURI.
		
		If the element is not contained by an XMLDocument, or the document does
		not have a fully specified baseURI then the return result may be a
		relative path or even None, if no base information is available."""
		baser=self
		baseURI=None
		while baser:
			rebase=baser.GetBase()
			if baseURI:
				baseURI=urlparse.urljoin(rebase,baseURI)
			else:
				baseURI=rebase
			if isinstance(baser,XMLElement):
				baser=baser.parent
			else:
				break
		return baseURI
				
	def ResolveURI(self,uri):
		r"""Returns a fully specified URL, resolving uri in the current context.
		
		The uri is resolved relative to the xml:base values of the element's
		ancestors and ultimately relative to the document's baseURI."""
		baseURI=self.ResolveBase()
		if baseURI:
			return URIFactory.Resolve(baseURI,uri)
		elif isinstance(uri,URI):
			return uri
		else:
			return URIFactory.URI(uri)
	
	def RelativeURI(self,href):
		"""Returns href expressed relative to the element's base.

		If href is a relative URI then it is converted to a fully specified URL
		by interpreting it as being the URI of a file expressed relative to the
		current working directory.

		If the element does not have a fully-specified base URL then href is
		returned as a fully-specified URL itself."""
		result=[]
		if not isinstance(href,URI):
			href=URIFactory.URI(href)
		if not href.IsAbsolute():
			href=href.Resolve(URIFactory.URLFromPathname(os.getcwd()))
		base=self.ResolveBase()
		if base is not None:
			return URIFactory.Relative(href,base)
# 			base=URIFactory.URI(base)
# 			if not base.IsAbsolute():
# 				return str(href)
# 			else:
# 				return str(href.Relative(base))
		else:
			return href

	def GetLang(self):
		return self._attrs.get(xml_lang,None)
	
	def SetLang(self,lang):
		if lang is None:
			self._attrs.pop(xml_lang,None)
		else:
			self._attrs[xml_lang]=lang

	def ResolveLang(self):
		"""Returns the effective language for the current element.
		
		The language is resolved using the xml:lang value of the element or its
		ancestors.  If no xml:lang is in effect then None is returned."""
		baser=self
		baseLang=None
		while baser:
			lang=baser.GetLang()
			if lang:
				return lang
			if isinstance(baser,XMLElement):
				baser=baser.parent
			else:
				break
		return None
	
	def GetSpace(self):
		return self._attrs.get(xml_space,None)
	
	def SetSpace(self,space):
		if space is None:
			self._attrs.pop(xml_space,None)
		else:
			self._attrs[xml_space]=space

	def PrettyPrint(self):
		"""Indicates if this element's content should be pretty-printed.
		
		This method is used when formatting XML files to text streams.  The
		behaviour can be affected by the xml:space attribute or by derived
		classes that can override the default behaviour.
		
		If this element has xml:space set to 'preserve' then we return False.
		If self.parent.PrettyPrint() returns False then we return False.
		
		Otherwise we return False if we know the element is (or should be) mixed
		content, True otherwise.
		
		Note: an element on undetermined content model that contains only elements
		and white space *is* pretty printed."""
		spc=self.GetSpace()
		if spc is not None and spc=='preserve':
			return False
		if hasattr(self.__class__,'SGMLCDATA'):
			return False
		if isinstance(self.parent,XMLElement):
			spc=self.parent.PrettyPrint()
			if spc is False:
				return False
		if hasattr(self.__class__,'XMLCONTENT'):
			# if we have a defined content model then we return False for
			# mixed content.
			return self.__class__.XMLCONTENT!=XMLMixedContent
		else:
			children=self.GetChildren()
			for child in self.GetChildren():
				if type(child) in StringTypes:
					for c in child:
						if not IsS(c):
							return False
		return True
		
	def WriteXMLAttributes(self,attributes,escapeFunction=EscapeCharData):
		"""Adds strings representing the element's attributes
		
		attributes is a list of unicode strings.  Attributes should be appended
		as strings of the form 'name="value"' with values escaped appropriately
		for XML output."""
		attrs=self.GetAttributes()
		keys=attrs.keys()
		self.SortNames(keys)
		for a in keys:
			attributes.append(u'%s=%s'%(a,escapeFunction(attrs[a],True)))
				
	def WriteXML(self,writer,escapeFunction=EscapeCharData,indent='',tab='\t'):
		if tab:
			ws='\n'+indent
			indent=indent+tab
		else:
			ws=''
		if not self.PrettyPrint():
			# inline all children
			indent=''
			tab=''
		attributes=[]
		self.WriteXMLAttributes(attributes,escapeFunction)
		if attributes:
			attributes[0:0]=['']
			attributes=string.join(attributes,' ')
		else:
			attributes=''
		children=self.GetCanonicalChildren()
		if children:
			if type(children[0]) in StringTypes and len(children[0])>0 and IsS(children[0][0]):
				# First character is WS, so assume pre-formatted
				indent=tab=''
			writer.write(u'%s<%s%s>'%(ws,self.xmlname,attributes))
			if hasattr(self.__class__,'SGMLCDATA'):
				# When expressed in SGML this element would have type CDATA so put it in a CDSect
				writer.write(EscapeCDSect(self.GetValue()))
			else:
				for child in children:
					if type(child) in types.StringTypes:
						# We force encoding of carriage return as these are subject to removal
						writer.write(escapeFunction(child))
						# if we have character data content skip closing ws
						ws=''
					else:
						child.WriteXML(writer,escapeFunction,indent,tab)
			if not tab:
				# if we weren't tabbing children we need to skip closing white space
				ws=''
			writer.write(u'%s</%s>'%(ws,self.xmlname))
		else:
			writer.write(u'%s<%s%s/>'%(ws,self.xmlname,attributes))
				

class XMLDocument(handler.ContentHandler, handler.ErrorHandler):
	def __init__(self, root=None, baseURI=None, **args):
		"""Initialises a new XMLDocument from optional keyword arguments.
		
		With no arguments, a new XMLDocument is created with no baseURI
		or root element.
		
		If root is a class object (descended from XMLElement) it is used
		to create the root element of the document.
		
		baseURI can be set on construction (see SetBase)
		"""
		self.parser=make_parser()
		self.parser.setFeature(handler.feature_namespaces,0)
		self.parser.setFeature(handler.feature_validation,0)
		self.parser.setContentHandler(self)
		self.parser.setErrorHandler(self)
		self.baseURI=None
		self.lang=None
		if root:
			if not issubclass(root,XMLElement):
				raise ValueError
			self.root=root(self)
		else:
			self.root=None
		self.SetBase(baseURI)
		self.parameterEntities={}
		#self.parser.setEntityResolver(self)
		self.idTable={}

	def __str__(self):
		"""Returns the XML document as a string"""
		s=StringIO()
		self.WriteXML(s,EscapeCharData7)
		return str(s.getvalue())
	
	def __unicode__(self):
		s=StringIO()
		self.WriteXML(s,EscapeCharData)
		return unicode(s.getvalue())
	
	def DeclareParameterEntity(self,name,value):
		self.parameterEntities[name]=value

	def GetParameterEntity(self,name):
		v=self.parameterEntities.get(name,None)
		if v is not None:
			return XMLEntity(v)
			
	def GetElementClass(self,name):
		"""Returns a class object suitable for representing name
		
		name is a unicode string representing the element name.
		
		The default implementation returns XMLElement."""
		return XMLElement

	def ChildElement(self,childClass,name=None):
		"""Creates the root element of the given document.
		
		The signature of this method matches the ChildElement method of
		XMLElement but no custom factory method mechanism exists.  If there
		is already a root element it is detached from the document first."""
		if self.root:
			self.root.DetachFromDocument()
			self.root.parent=None
			self.root=None
		child=childClass(self)
		if name:
			child.SetXMLName(name)
		self.root=child
		return self.root
		
	def SetBase(self,baseURI):
		"""Sets the baseURI of the document to the given URI.
		
		If the baseURI is a local file or relative path then the file path
		is updated to point to the file."""
		if baseURI is None:
			self.baseURI=None
		else:
			if isinstance(baseURI,URI):
				self.baseURI=baseURI
			else:
				self.baseURI=URIFactory.URI(baseURI)
			if not self.baseURI.IsAbsolute():
				cwd=URIFactory.URLFromPathname(os.path.join(os.getcwd(),os.curdir))
				self.baseURI=self.baseURI.Resolve(cwd)
			
	def GetBase(self):
		if self.baseURI is None:
			return None
		else:
			return str(self.baseURI)
	
	def SetLang(self,lang):
		"""Sets the default language for the document."""
		self.lang=lang
	
	def GetLang(self):
		"""Returns the default language for the document."""
		return self.lang
			
	def ValidationError(self,msg,element,data=None,aname=None):
		"""Called when a validation error is triggered by element.

		This method is designed to be overriden to implement custom error
		handling or logging (which is likely to be added in future to this
		module).

		msg contains a brief message suitable for describing the error in a log
		file.  data and aname have the same meanings as
		XMLElement.ValidationError."""
		raise XMLValidationError("%s (in %s)"%(msg,element.xmlname))
		
	def RegisterElement(self,element):
		if self.idTable.has_key(element.id):
			raise XMLIDClashError
		else:
			self.idTable[element.id]=element
	
	def UnregisterElement(self,element):
		if element.id:
			del self.idTable[element.id]
	
	def GetElementByID(self,id):
		return self.idTable.get(id,None)
	
	def GetUniqueID (self,baseStr=None):
		if not baseStr:
			baseStr='%X'%random.randint(0,0xFFFF)
		idStr=baseStr
		idExtra=0
		while self.idTable.has_key(idStr):
			if not idExtra:
				idExtra=random.randint(0,0xFFFF)
			idStr='%s-%X'%(baseStr,idExtra)
			idExtra=idExtra+1
		return idStr

	def Read(self,src=None,reqManager=None,**args):
		if src:
			# Read from this stream, ignore baseURI
			if isinstance(src,XMLEntity):
				self.ReadFromEntity(src)
			else:
				self.ReadFromStream(src)
		elif self.baseURI is None:
			raise XMLMissingLocationError
		else:
			e=XMLEntity(self.baseURI)
			self.ReadFromEntity(e)
# 		elif isinstance(self.baseURI,FileURL):
# 			# we would need to force 8bit path names to workaround bug in expat
# 			# but we've ditched sax so we don't have to do this anymore
# 			f=open(self.baseURI.GetPathname(),'rb')
# 			try:
# 				self.ReadFromStream(f)
# 			finally:
# 				f.close()
# 		elif self.baseURI.scheme.lower() in ['http','https']:
# 			if reqManager is None:
# 				reqManager=http.HTTPRequestManager()
# 			req=http.HTTPRequest(str(self.baseURI))
# 			reqManager.ProcessRequest(req)
# 			if req.status==200:
# 				mtype=req.response.GetContentType()
# 				if mtype is None:
# 					# We'll attempt to do this with xml and utf8
# 					charset='utf8'
# 					raise UnimplementedError
# 				else:
# 					mimetype=mtype.type.lower()+'/'+mtype.subtype.lower()
# 					#if not ValidateXMLMimeType(mimetype):
# 					#	raise XMLContentTypeError(mimetype)
# 					self.ReadFromStream(StringIO(req.resBody))
# 			else:
# 				raise XMLUnexpectedHTTPResponse(str(req.status))
# 		else:
# 			raise XMLUnsupportedScheme
	
	def ReadFromStream(self,src):
		self.cObject=self
		self.objStack=[]
		self.data=[]
		#self.parser.parse(src)
		e=XMLEntity(src)
		self.ReadFromEntity(e)
		
	def ReadFromEntity(self,e):
		self.cObject=self
		self.objStack=[]
		self.data=[]
		parser=XMLParser(e)
		parser.ParseDocument(self)
		
	def startElement(self, name, attrs):
		parent=self.cObject
		self.objStack.append(self.cObject)
		if self.data:
			parent.AddData(string.join(self.data,''))
			self.data=[]
		eClass=self.GetElementClass(name)
		self.cObject=parent.ChildElement(eClass,name)
		for attr in attrs.keys():
			self.cObject.SetAttribute(attr,attrs[attr])

	def characters(self,ch):
		self.data.append(ch)
			
	def endElement(self,name):
		if self.objStack:
			parent=self.objStack.pop()
		else:
			parent=None
		if self.data:
			self.cObject.AddData(string.join(self.data,''))
			self.data=[]
		self.cObject.GotChildren()
		self.cObject=parent
			
	def Create(self,dst=None,**args):
		"""Creates the XMLDocument.
		
		Create outputs the document as an XML stream.  The stream is written
		to the baseURI by default but if the 'dst' argument is provided then
		it is written directly to there instead.  dst can be any object that
		supports the writing of unicode strings.
		
		Currently only documents with file type baseURIs are supported.  The
		file's parent directories are created if required.  The file is
		always written using the UTF-8 as per the XML standard."""
		if dst:
			self.WriteXML(dst)
		elif self.baseURI is None:
			raise XMLMissingLocationError
		elif isinstance(self.baseURI,FileURL):
			fPath=self.baseURI.GetPathname()
			fdir,fname=os.path.split(fPath)
			if not os.path.isdir(fdir):
				os.makedirs(fdir)
			f=codecs.open(fPath,'wb','utf-8')
			try:
				self.WriteXML(f)
			finally:
				f.close()
		else:
			raise XMLUnsupportedSchemeError(self.baseURI.scheme)
	
	def WriteXML(self,writer,escapeFunction=EscapeCharData,tab='\t'):
		if tab:
			writer.write(u'<?xml version="1.0" encoding="UTF-8"?>')
		else:
			writer.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')
		if self.root:
			self.root.WriteXML(writer,escapeFunction,'',tab)
	
	def Update(self,**args):
		"""Updates the XMLDocument.
		
		Update outputs the document as an XML stream.  The stream is written
		to the baseURI which must already exist!  Currently only documents
		with file type baseURIs are supported."""
		if self.baseURI is None:
			raise XMLMissingLocationError
		elif isinstance(self.baseURI,FileURL):
			fPath=self.baseURI.GetPathname()
			if not os.path.isfile(fPath):
				raise XMLMissingFileError(fPath)
			f=codecs.open(fPath,'wb','utf-8')
			try:
				self.WriteXML(f)
			finally:
				f.close()
		else:
			raise XMLUnsupportedSchemeError(self.baseURI.scheme)		
	
	def Delete(self,reqManager=None):
		pass

	def DiffString(self,otherDoc,before=10,after=5):
		"""Compares this document to otherDoc and returns first point of difference."""
		lines=str(self).split('\n')
		otherLines=str(otherDoc).split('\n')
		output=[]
		i=0
		iDiff=None
		while i<len(lines) and i<len(otherLines):
			if i>=len(lines):
				line=''
			else:
				line=lines[i]
			if i>=len(otherLines):
				otherLine=''
			else:
				otherLine=otherLines[i]
			if line==otherLine:
				i=i+1
				continue
			else:
				# The strings differ from here.
				iDiff=i
				break
		if iDiff is None:
			return None
		for i in xrange(iDiff-before,iDiff):
			if i<0:
				continue
			if i>=len(lines):
				line='[%3i] **EOF**'%i
			else:
				line='[%3i] '%i+lines[i]
			output.append(line)
		output.append('>>>>> Showing %i lines of difference'%after)
		for i in xrange(iDiff,iDiff+after):
			if i>=len(lines):
				line='[%3i] **EOF**'%i
			else:
				line='[%3i] '%i+repr(lines[i])
			output.append(line)
		output.append('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
		for i in xrange(iDiff,iDiff+after):
			if i>=len(otherLines):
				line='[%3i] **EOF**'%i
			else:
				line='[%3i] '%i+repr(otherLines[i])
			output.append(line)
		return string.join(output,'\n')


def MapClassElements(classMap,namespace):
	"""Searches namespace and adds element name -> class mappings to classMap
	
	If namespace is none the current namespace is searched.  The search is
	not recursive, to add class elements from imported modules you must call
	MapClassElements for each module."""
	if type(namespace) is not DictType:
		namespace=namespace.__dict__
	names=namespace.keys()
	for name in names:
		obj=namespace[name]
		if type(obj) is ClassType and issubclass(obj,XMLElement):
			if hasattr(obj,'XMLNAME'):
				classMap[obj.XMLNAME]=obj


def ParseXMLClass(classDefStr):
	"""The purpose of this function is to provide a convenience for creating character
	class definitions from the XML specification documents.  The format of those
	declarations is along these lines (this is the definition for Char):

	#x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
	
	We parse strings in this format into a character class and then print out a
	declaration of it suitable for including in code."""
	c=CharClass()
	definitions=classDefStr.split('|')
	for d in definitions:
		hexStr=[]
		for di in d:
			if di in '[]#x':
				continue
			else:
				hexStr.append(di)
		rangeDef=map(lambda x:int(x,16),string.split(string.join(hexStr,''),'-'))
		if len(rangeDef)==1:
			a=rangeDef[0]
			if a>maxunicode:
				print "Warning: character outside narrow python build (%X)"%a
			else:
				c.AddChar(unichr(a))
		elif len(rangeDef)==2:
			a,b=rangeDef
			if a>maxunicode:
				print "Warning: character range outside narrow python build (%X-%X)"%(a,b)
			elif b>maxunicode:
				print "Warning: character range truncated due to narrow python build (%X-%X)"%(a,b)
				b=maxunicode
				c.AddRange(unichr(a),unichr(b))
			else:
				c.AddRange(unichr(a),unichr(b))			
	print repr(c)
