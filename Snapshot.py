from io import BytesIO

import Cluster
import Constants

from ClassId import ClassId
from Kind import Kind
from Utils import *

class Snapshot:
	# snapshot = byte array of VM snapshot
	# magic = snapshot header (size: kHeaderSize)
	# size = snapshot's length in bytes
	# kind = snapshot's kind (enum)
	# hash = version hash (32 byte string)
	# features = string array of features
 
	def __init__(self, snapshot):
		# Header
		self.stream = BytesIO(snapshot)
		self.magic = int.from_bytes(self.stream.read(Constants.kMagicSize), 'little')
		self.size = int.from_bytes(self.stream.read(Constants.kLengthSize), 'little')
		self.kind = Kind(int.from_bytes(self.stream.read(Constants.kKindSize), 'little'))
		self.hash = self.stream.read(Constants.hashSize).decode('UTF-8')
		self.features = list(map(lambda x: x.decode('UTF-8'), StreamUtils.readString(self.stream).split(b'\x20')))
		
		# Set up deterministic information
		self.isProduct = 'product' in self.features
		self.hasComments = False #FIXME
		self.isPrecompiled = self.kind == Kind.FULL_AOT and 'product' in self.features
		self.isDebug = 'debug' in self.features
		self.useBareInstructions = 'use_bare_instructions' in self.features
		self.includesCode = self.kind == Kind.FULL_JIT or self.kind == Kind.FULL_AOT
		self.instructionsImage = 0 #FIXME
		self.previousTextOffset = 0
		if 'x64-sysv' in self.features:
			self.arch = 'X64'
			Constants.kMonomorphicEntryOffsetAOT = 8
			Constants.kPolymorphicEntryOffsetAOT = 22
		elif 'arm64-sysv' in self.features:
			self.arch = 'ARM64'
			Constants.kMonomorphicEntryOffsetAOT = 8
			Constants.kPolymorphicEntryOffsetAOT = 20
		else:
			raise Exception('Unknown architecture')

		# Cluster information
		self.numBaseObjects = StreamUtils.readUnsigned(self.stream)
		self.numObjects = StreamUtils.readUnsigned(self.stream)
		self.numClusters = StreamUtils.readUnsigned(self.stream)
		self.fieldTableLength = StreamUtils.readUnsigned(self.stream)

		# Initialize references
		self.references = ['INVALID'] # Reference count starts at 1
		self.nextRefIndex = 1
		self.addBaseObjects()
		for _ in range(len(self.references), self.numBaseObjects):
			self.assignRef('UNKNOWN') # Allocate missing references

		self.unboxedFieldsMapAt = { }

		assert(len(self.references) == self.numBaseObjects)

		self.clusters = [ self.readClusterAlloc() for _ in range(self.numClusters) ]

		assert(len(self.references) == self.numObjects)

		for cluster in self.clusters:
			cluster.readFill(self)

		self.readRoots()

		self.dataImageOffset = NumericUtils.roundUp(self.length(), Constants.kMaxObjectAlignment)

	def addBaseObjects(self):
		baseObjects = [
			'Null',
			'Sentinel',
			'TransitionSentinel',
			'EmptyArray',
			'ZeroArray',
			'DynamicType',
			'VoidType',
			'EmptyTypeArguments',
			'True',
			'False',
			'ExtractorParameterTypes',
			'ExtractorParameterNames',
			'EmptyContextScope',
			'EmptyDescriptors',
			'EmptyVarDescriptors',
			'EmptyExceptionHandlers',
			'ImplicitGetterBytecode',
			'ImplicitSetterBytecode',
			'ImplicitStaticGetterBytecode',
			'MethodExtractorBytecode',
			'InvokeClosureBytecode',
			'InvokeFieldBytecode',
			'NsmDispatcherBytecode',
			'DynamicInvocationForwarderBytecode',
			*('CachedArgsDescriptors' for _ in range(Constants.kCachedDescriptorCount)),
			*('CachedICDataArrays' for _ in range(Constants.kCachedICDataArrayCount)),
			'CachedArray',
			*('ClassStub' for cid in range(ClassId.CLASS.value, ClassId.UNWIND_ERROR.value + 1) if (cid != ClassId.ERROR.value and cid != ClassId.CALL_SITE_DATA.value)),
			'Dynamic CID',
			'VoidCID',
			*('StubCode' for _ in range(Constants.kNumStubEntries) if not Snapshot.includesCode(self.kind))
		]
		for obj in baseObjects:
			self.assignRef(obj)

	def readRoots(self):
		self.symbolTable = StreamUtils.readRef(self.stream)
		print(self.symbolTable)
		print(self.references[47809])

	def assignRef(self, obj):
		self.references.append(obj)
		self.nextRefIndex += 1

	def readClusterAlloc(self):
		deserializer = Cluster.getDeserializerForCid(self.includesCode, StreamUtils.readCid(self.stream))
		deserializer.readAlloc(self)
		return deserializer

	# Getter of the snapshot's header
	def getMagic(self):
		return self.magic
 
	# Getter of the snapshot's size
	def getSize(self):
		return self.size
 
	# Getter of the snapshot's kind
	def getKind(self):
		return self.kind
 
	# Getter of the snapshot's version
	def getHash(self):
		return self.hash
 
	# Getter of the snapshot's features
	def getFeatures(self):
		return self.features
 
	# Getter of the snapshot's base objects count
	def getNumBaseObjects(self):
		return self.numBaseObjects
 
	# Getter of the snapshot's objects count
	def getNumObjects(self):
		return self.numObjects
 
	# Getter of the snapshot's clusters count
	def getNumClusters(self):
		return self.numClusters
 
	# Getter of the snapshot's clusters count
	def getFieldTableLength(self):
		return self.fieldTableLength
 
	# Getter of the snapshot's data image offset
	def getDataImageOffset(self):
		return self.dataImageOffset
 
	def length(self):
		return self.getSize() + Constants.kMagicSize

	def includesCode(kind):
		return (kind is Kind.FULL_JIT) or (kind is Kind.FULL_AOT)
 
	# Pretty printable string of the snapshot's main characteristics
	def getSummary(self):
		prettyString = 'Magic: 0xf5f5dcdc' + '\n'
		prettyString += 'Snapshot size (including ' + str(Constants.kMagicSize) + 'B of magic): ' + str(self.length()) + 'B\n'
		prettyString += 'Kind: ' + str(self.getKind()) + '\n'
		prettyString += 'Version: ' + self.getHash() + ' (' + getVersionInfo(self.getHash()) + ')\n'
		prettyString += 'Features: ' + ', '.join(self.getFeatures()) + '\n'
		prettyString += 'Base objects count: ' + str(self.getNumBaseObjects()) + '\n'
		prettyString += 'Objects count: ' + str(self.getNumObjects()) + '\n'
		prettyString += 'Clusters count: ' + str(self.getNumClusters()) + '\n'
		prettyString += 'Field table length: ' + str(self.getFieldTableLength()) + '\n'
		prettyString += 'Data image offset: ' + str(self.getDataImageOffset())
		return prettyString