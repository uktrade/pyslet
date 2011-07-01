#! /usr/bin/env python


import string

XMLSCHEMA_NAMESPACE="http://www.w3.org/2001/XMLSchema-instance"

def DecodeBoolean(src):
	"""Decodes a boolean value from src.
	
	Returns python constants True or False.  As a convenience, if src is None
	then None is returned."""
	if src is None:
		return None
	elif src=="true":
		return True
	elif src=="false":
		return False
	elif src=="1":
		return True
	elif src=="0":
		return False
	else:
		raise ValueError

def EncodeBoolean(src):
	"""Encodes a boolean value using the canonical lexical representation.
	
	src can be anything that can be resolved to a boolean except None, which
	raises ValueError."""
	if src is None:
		raise ValueError
	elif src:
		return "true"
	else:
		return "false"


def DecodeInteger(src):
	try:
		return int(src)
	except:
		return None

def EncodeInteger(value):
	return unicode(value)


def DecodeFloat(src):
	try:
		return float(src)
	except:
		return None

def EncodeFloat(value):
	return unicode(value)


def MakeEnumeration(e):
	"""Adds convenience attributes to the class 'e'
	
	This function assumes that e has an attribute 'decode' that is a dictionary
	which maps strings onto enumeration values.  This function creates the reverse
	mapping called 'encode' and also defines constant attribute values that are
	equivalent to the keys of decode and can be used in code in the form e.key."""
	setattr(e,'encode',dict(zip(e.decode.values(),e.decode.keys())))
	map(lambda x:setattr(e,x,e.decode[x]),e.decode.keys())


def WhiteSpaceReplace(value):
	output=[]
	for c in value:
		if c in u"\x09\x0A\x0D":
			output.append(unichr(0x20))
		else:
			output.append(c)
	return string.join(output,'')


def WhiteSpaceCollapse(value):
	output=[]
	gotSpace=False
	for c in value:
		if c in u"\x09\x0A\x0D\x20":
			gotSpace=True
		else:
			if output and gotSpace:
				output.append(unichr(0x20))
				gotSpace=False
			output.append(c)
	return string.join(output,'')