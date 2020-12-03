import Constants

from ClassId import ClassId
from Kind import Kind
import TypedData
from UnboxedFieldBitmap import UnboxedFieldBitmap
from Utils import DecodeUtils, NumericUtils, StreamUtils, isTopLevelCid

def getDeserializerForCid(includesCode, cid):
	# Class ID: 4
	class ClassDeserializer():
		def readAlloc(self, snapshot):
			self.predefinedStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				classId = StreamUtils.readCid(snapshot.stream)
				snapshot.assignRef('class')
			self.predefinedStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('instance size')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.predefinedStartIndex, self.predefinedStopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				# The two next fields are skipped IsInternalVMdefinedClassId fails
				# for the current class ID. Assigning them should be irrelevant.
				classPtr['hostInstanceSizeInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostNextFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostTypeArgumentsFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)

				if not snapshot.isPrecompiled:
					classPtr['targetInstanceSizeInWords'] = classPtr['hostInstanceSizeInWords']
					classPtr['targetNextFieldOffsetInWords'] = classPtr['hostNextFieldOffsetInWords']
					classPtr['targetTypeArgumentsFieldOffsetInWords'] = classPtr['hostTypeArgumentsFieldOffsetInWords']

				classPtr['numTypeArguments'] = StreamUtils.readInt(snapshot.stream, 16)
				classPtr['numNativeFields'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				classPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['stateBits'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if snapshot.isPrecompiled:
					StreamUtils.readUnsigned(snapshot.stream, 64)

				snapshot.references[refId] = classPtr

			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				classId = StreamUtils.readCid(snapshot.stream)
				classPtr['id'] = classId

				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)
				classPtr['hostInstanceSizeInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostNextFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)
				classPtr['hostTypeArgumentsFieldOffsetInWords'] = StreamUtils.readInt(snapshot.stream, 32)

				if not snapshot.isPrecompiled:
					classPtr['targetInstanceSizeInWords'] = classPtr['hostInstanceSizeInWords']
					classPtr['targetNextFieldOffsetInWords'] = classPtr['hostNextFieldOffsetInWords']
					classPtr['targetTypeArgumentsFieldOffsetInWords'] = classPtr['hostTypeArgumentsFieldOffsetInWords']

				classPtr['numTypeArguments'] = StreamUtils.readInt(snapshot.stream, 16)
				classPtr['numNativeFields'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				classPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				classPtr['stateBits'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if snapshot.isPrecompiled and not isTopLevelCid(classId):
					snapshot.unboxedFieldsMapAt[classId] = UnboxedFieldBitmap(StreamUtils.readUnsigned(snapshot.stream, 64))

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { }
			classPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['userName'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['functions'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['functionsHashTable'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['fields'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['offsetInWordsToField'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['interfaces'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['library'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['superType'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['signatureFunction'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['constants'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['declarationType'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['invocationDispatcherCache'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['allocationStub'] = StreamUtils.readUnsigned(snapshot.stream)
			if not (snapshot.kind is Kind.FULL_AOT):
				classPtr['directImplementors'] = StreamUtils.readUnsigned(snapshot.stream)
				if not (snapshot.kind is Kind.FULL):
					classPtr['directSubclasses'] = StreamUtils.readUnsigned(snapshot.stream)
					if not (snapshot.kind is Kind.FULL_JIT):
						classPtr['dependentCode'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 5
	class PatchClassDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('patch class')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				classPtr = self._readFromTo(snapshot)
				if (not snapshot.isPrecompiled) and (not snapshot.kind is Kind.FULL_AOT):
					classPtr['libraryKernelOffset'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = classPtr

		def _readFromTo(self, snapshot):
			classPtr = { }
			classPtr['patchedClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['originClass'] = StreamUtils.readUnsigned(snapshot.stream)
			classPtr['script'] = StreamUtils.readUnsigned(snapshot.stream)
			if not snapshot.kind is Kind.FULL_AOT:
				classPtr['libraryKernelData'] = StreamUtils.readUnsigned(snapshot.stream)
			return classPtr

	# Class ID: 6
	class FunctionDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('function')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				funcPtr = self._readFromTo(snapshot)
				if (snapshot.kind is Kind.FULL):
					#TODO
					raise Exception('Not implemented')
				elif (snapshot.kind is Kind.FULL_AOT):
					funcPtr['code'] = StreamUtils.readRef(snapshot.stream)
				else:
					#TODO
					raise Exception('Not implemented')

				#TODO: if debug

				if not snapshot.isPrecompiled:
					if not snapshot.kind is Kind.FULL_AOT:
						funcPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
						funcPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
						funcPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)
					#TODO: reset

				funcPtr['packedFields'] = StreamUtils.readUnsigned(snapshot.stream, 32)
				funcPtr['kindTag'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				if (not snapshot.kind is Kind.FULL_AOT) and (not snapshot.isPrecompiled):
					funcPtr['usageCounter'] = 0
					funcPtr['optimizedInstructionCount'] = 0
					funcPtr['optimizedCallSiteCount'] = 0
					funcPtr['deoptimizationCounter'] = 0
					funcPtr['stateBits'] = 0
					funcPtr['inliningDepth'] = 0

				snapshot.references[refId] = funcPtr

		def _readFromTo(self, snapshot):
			funcPtr = { }
			funcPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['resultType'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterTypes'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['parameterNames'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['typeParameters'] = StreamUtils.readUnsigned(snapshot.stream)
			funcPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

			return funcPtr

	# Class ID: 7
	class ClosureDataDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('closure data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				closureDataPtr = { }

				if (snapshot.kind is Kind.FULL_AOT):
					closureDataPtr['contextScope'] = None
				else:
					closureDataPtr['contextScope'] = StreamUtils.readRef(snapshot.stream)

				closureDataPtr['parentFunction'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['signatureType'] = StreamUtils.readRef(snapshot.stream)
				closureDataPtr['closure'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = closureDataPtr

	# Class ID: 8
	class SignatureDataDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('signature data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				dataPtr = self._readFromTo(snapshot)

				snapshot.references[refId] = dataPtr

		def _readFromTo(self, snapshot):
			dataPtr = { }
			dataPtr['parentFunction'] = StreamUtils.readUnsigned(snapshot.stream)
			dataPtr['signatureType'] = StreamUtils.readUnsigned(snapshot.stream)

			return dataPtr

	# Class ID: 11
	class FieldDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('field')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				fieldPtr = self._readFromTo(snapshot)

				if snapshot.kind is not Kind.FULL_AOT:
					if not snapshot.isPrecompiled:
						fieldPtr['savedInitialValue'] = StreamUtils.readRef(snapshot.stream)
					fieldPtr['guardedListLength'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is Kind.FULL_JIT:
					fieldPtr['dependentCode'] = StreamUtils.readRef(snapshot.stream)

				if snapshot.kind is not Kind.FULL_AOT:
					fieldPtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['endTokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
					fieldPtr['guardedCid'] = StreamUtils.readCid(snapshot.stream)
					fieldPtr['isNullable'] = StreamUtils.readCid(snapshot.stream)
					fieldPtr['staticTypeExactnessState'] = StreamUtils.readInt(snapshot.stream, 8)
					if not snapshot.isPrecompiled:
						fieldPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				fieldPtr['kindBits'] = StreamUtils.readUnsigned(snapshot.stream, 16)

				valueOrOffset = StreamUtils.readRef(snapshot.stream)
				if DecodeUtils.decodeStaticBit(fieldPtr['kindBits']):
					fieldId = StreamUtils.readUnsigned(snapshot.stream)
					fieldPtr['hostOffsetOrFieldId'] = ('Smi', fieldId)
				else:
					fieldPtr['hostOffsetOrFieldId'] = ('Smi', valueOrOffset)
					if not snapshot.isPrecompiled:
						fieldPtr['targetOffset'] = ('Smi', fieldPtr['hostOffsetOrFieldId'])

				snapshot.references[refId] = fieldPtr

		def _readFromTo(self, snapshot):
			fieldPtr = { }
			fieldPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['owner'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['type'] = StreamUtils.readUnsigned(snapshot.stream)
			fieldPtr['initializerFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return fieldPtr

	# Class ID: 12
	class ScriptDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('script')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				scriptPtr = self._readFromTo(snapshot)

				scriptPtr['lineOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['colOffset'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['flags'] = StreamUtils.readUnsigned(snapshot.stream, 8)
				scriptPtr['kernelScriptIndex'] = StreamUtils.readInt(snapshot.stream, 32)
				scriptPtr['loadTimestamp'] = 0

				snapshot.references[refId] = scriptPtr

		def _readFromTo(self, snapshot):
			scriptPtr = { }
			scriptPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)

			if snapshot.kind is Kind.FULL or snapshot.kind is Kind.FULL_JIT:
				scriptPtr['resolvedUrl'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['compileTimeConstants'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['lineStarts'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['debugPositions'] = StreamUtils.readUnsigned(snapshot.stream)
				scriptPtr['kernelProgramInfo'] = StreamUtils.readUnsigned(snapshot.stream)

			return scriptPtr

	# Class ID: 13
	class LibraryDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('library')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				libraryPtr = self._readFromTo(snapshot)
				libraryPtr['nativeEntryResolver'] = None
				libraryPtr['nativeEntrySymbolResolver'] = None
				libraryPtr['index'] = StreamUtils.readInt(snapshot.stream, 32)
				libraryPtr['numImports'] = StreamUtils.readUnsigned(snapshot.stream, 16)
				libraryPtr['loadState'] = StreamUtils.readInt(snapshot.stream, 8)

				#TODO: missing update
				libraryPtr['flags'] = StreamUtils.readUnsigned(snapshot.stream, 8)

				if (not snapshot.isPrecompiled) and (snapshot.kind is not Kind.FULL_AOT):
					libraryPtr['binaryDeclaration'] = StreamUtils.readUnsigned(snapshot.stream, 32)

				snapshot.references[refId] = libraryPtr

		def _readFromTo(self, snapshot):
			libraryPtr = { }
			libraryPtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['url'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['privateKey'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['dictionary'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['metadata'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['toplevelClass'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['usedScripts'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['loadingUnit'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['imports'] = StreamUtils.readUnsigned(snapshot.stream)
			libraryPtr['exports'] = StreamUtils.readUnsigned(snapshot.stream)
			if (snapshot.kind is Kind.FULL) or (snapshot.kind is Kind.FULL_JIT):
				libraryPtr['dependencies'] = StreamUtils.readUnsigned(snapshot.stream)
				libraryPtr['kernelData'] = StreamUtils.readUnsigned(snapshot.stream)

			return libraryPtr

	# Class ID: 16
	class CodeDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('code')
			self.stopIndex = self.deferredStartIndex = snapshot.nextRefIndex
			deferredCount = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(deferredCount):
				snapshot.assignRef('code')
			self.deferredStopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				codePtr = self._readFill(snapshot, refId, False)
				snapshot.references[refId] = codePtr
			for refId in range(self.deferredStartIndex, self.deferredStopIndex):
				cdPtr = self._readFill(snapshot, refId, True)
				snapshot.references[refId] = codePtr

		def _readFill(self, snapshot, refId, deferred):
			codePtr = { }
			self._readInstructions(snapshot, codePtr, deferred)

			if not (snapshot.kind is Kind.FULL_AOT and snapshot.useBareInstructions):
				codePtr['objectPool'] = StreamUtils.readRef(snapshot.stream)
			else:
				codePtr['objectPool'] = None
			codePtr['owner'] = StreamUtils.readRef(snapshot.stream)
			codePtr['exceptionHandlers'] = StreamUtils.readRef(snapshot.stream)
			codePtr['pcDescriptors'] = StreamUtils.readRef(snapshot.stream)
			codePtr['catchEntry'] = StreamUtils.readRef(snapshot.stream)
			codePtr['compressedStackMaps'] = StreamUtils.readRef(snapshot.stream)
			codePtr['inlinedIdToFunction'] = StreamUtils.readRef(snapshot.stream)
			codePtr['codeSourceMap'] = StreamUtils.readRef(snapshot.stream)

			if (not snapshot.isPrecompiled) and (snapshot.kind is Kind.FULL_JIT):
				codePtr['deoptInfoArray'] = StreamUtils.readRef(snapshot.stream)
				codePtr['staticCallsTargetTable'] = StreamUtils.readRef(snapshot.stream)

			if not snapshot.isProduct:
				codePtr['returnAddressMetadata'] = StreamUtils.readRef(snapshot.stream)
				codePtr['varDescriptors'] = None
				codePtr['comments'] = StreamUtils.readRef(snapshot.stream) if snapshot.hasComments else []
				codePtr['compileTimestamp'] = 0

			codePtr['stateBits'] = StreamUtils.readInt(snapshot.stream, 32)

			return codePtr

		def _readInstructions(self, snapshot, codePtr, deferred):
			if deferred:
				if snapshot.isPrecompiled and snapshot.useBareInstructions:
					codePtr['entryPoint'] = 'entryPoint'
					codePtr['uncheckedEntryPoint'] = 'entryPoint'
					codePtr['monomorphicEntryPoint'] = 'entryPoint'
					codePtr['monomorphicUncheckedEntryPoint'] = 'entryPoint'
					codePtr['instructionsLength'] = 0
					return
				codePtr['uncheckedOffset'] = 0
				#TODO: cahed entry points
				return

			if snapshot.isPrecompiled and snapshot.useBareInstructions:
				snapshot.previousTextOffset += StreamUtils.readUnsigned(snapshot.stream)
				payloadStart = snapshot.instructionsImage + snapshot.previousTextOffset
				payloadInfo = StreamUtils.readUnsigned(snapshot.stream)
				uncheckedOffset = payloadInfo >> 1
				hasMonomorphicEntrypoint = (payloadInfo & 1) == 1

				entryOffset = Constants.kPolymorphicEntryOffsetAOT if hasMonomorphicEntrypoint else 0
				monomorphicEntryOffset = Constants.kMonomorphicEntryOffsetAOT if hasMonomorphicEntrypoint else 0
				entryPoint = payloadStart + entryOffset
				monomorphicEntryPoint = payloadStart + monomorphicEntryOffset

				codePtr['entryPoint'] = entryPoint
				codePtr['uncheckedEntryPoint'] = entryPoint + uncheckedOffset
				codePtr['monomorphicEntryPoint'] = monomorphicEntryPoint
				codePtr['monomorphicUncheckedEntryPoint'] = monomorphicEntryPoint + uncheckedOffset

				return

			#TODO


	# Class ID: 20
	class ObjectPoolDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('object pool')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				poolPtr = { }
				length = StreamUtils.readUnsigned(snapshot.stream)
				poolPtr['length'] = length
				poolPtr['entryBits'] = [ ]
				poolPtr['data'] = [ ]
				for j in range(length):
					entryBits = StreamUtils.readUnsigned(snapshot.stream, 8)
					poolPtr['entryBits'].append(entryBits)
					entry = { }
					decodedBits = DecodeUtils.decodeTypeBits(entryBits)
					if decodedBits == Constants.kNativeEntryData or decodedBits == Constants.kTaggedObject:
						entry['rawObj'] = StreamUtils.readRef(snapshot.stream)
					elif decodedBits == Constants.kImmediate:
						entry['rawValue'] = StreamUtils.readInt(snapshot.stream, 64)
					elif decodedBits == Constants.kNativeFunction:
						entry['rawValue'] = 'native call entry'
					else:
						raise Exception('No type associated to decoded type bits')
					poolPtr['data'].append(entry)

				snapshot.references[refId] = poolPtr

	# Class ID: 21
	class PcDescriptorsDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('pc descriptors')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				descPtr = { }
				descPtr['length'] = length
				descPtr['data'] = snapshot.stream.read(length)

				snapshot.references[refId] = descPtr

	# Aggregate deserializer for class IDs: 22, 23, 81, 82
	class RODataDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			runningOffset = 0
			for _ in range(count):
				runningOffset += StreamUtils.readUnsigned(snapshot.stream) << Constants.kObjectAlignmentLog2
				snapshot.assignRef('ro data object')

		def readFill(self, snapshot):
			return

	# Class ID: 25
	class ExceptionHandlersDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('exception')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				handlersPtr = { }
				handlersPtr['numEntries'] = length
				handlersPtr['handledTypesData'] = StreamUtils.readRef(snapshot.stream)
				data = []
				for j in range(length):
					info = { }
					info['handlerPcOffset'] = StreamUtils.readUnsigned(snapshot.stream, 32)
					info['outerTryIndex'] = StreamUtils.readInt(snapshot.stream, 16)
					# Original code has read int8
					info['needsStacktrace'] = StreamUtils.readBool(snapshot.stream)
					info['hasCatchAll'] = StreamUtils.readBool(snapshot.stream)
					info['isGenerated'] = StreamUtils.readBool(snapshot.stream)
					data.append(info)
				handlersPtr['data'] = data

				snapshot.references[refId] = handlersPtr

	# Class ID: 30
	class UnlinkedCallDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('unlinked call')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				unlinkedPtr = self._readFromTo(snapshot)
				unlinkedPtr['canPatchToMonomorphic'] = StreamUtils.readBool(snapshot.stream)

				snapshot.references[refId] = unlinkedPtr

		def _readFromTo(self, snapshot):
			unlinkedPtr = { }
			unlinkedPtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			unlinkedPtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)

			return unlinkedPtr

	# Class ID: 34
	class MegamorphicCacheDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('megamorphic cache')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = self._readFromTo(snapshot)
				cachePtr['filledEntryCount'] = StreamUtils.readInt(snapshot.stream, 32)

				snapshot.references[refId] = cachePtr

		def _readFromTo(self, snapshot):
			cachePtr = { }
			cachePtr['targetName'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['argsDescriptor'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['buckets'] = StreamUtils.readUnsigned(snapshot.stream)
			cachePtr['mask'] = StreamUtils.readUnsigned(snapshot.stream)

			return cachePtr

	# Class ID: 35
	class SubtypeTestCacheDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('subtype test cache')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				cachePtr = { }
				cachePtr['cache'] = StreamUtils.readRef(snapshot.stream)

				snapshot.references[refId] = cachePtr

	# Class ID: 35
	class LoadingUnitDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('loading unit')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				unitPtr = { }
				unitPtr['parent'] = StreamUtils.readRef(snapshot.stream)
				unitPtr['baseObjects'] = None
				unitPtr['id'] = StreamUtils.readInt(snapshot.stream, 32)
				unitPtr['loaded'] = False
				unitPtr['loadOutstanding'] = False

				snapshot.references[refId] = unitPtr

	# Class ID: 42
	class InstanceDeserializer():
		def __init__(self, cid):
			self.cid = cid

		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			self.nextFieldOffsetInWords = StreamUtils.readInt(snapshot.stream, 32)
			self.instanceSizeInWords = StreamUtils.readInt(snapshot.stream, 32)
			for _ in range(count):
				snapshot.assignRef('instance')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			nextFieldOffset = self.nextFieldOffsetInWords << Constants.kWordSizeLog2
			instanceSize = NumericUtils.roundUp(self.instanceSizeInWords * Constants.kWordSize, Constants.kObjectAlignment)
			for refId in range(self.startIndex, self.stopIndex):
				instancePtr = { }
				instancePtr['data'] = []
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				offset = 8
				while offset < nextFieldOffset:
					if snapshot.unboxedFieldsMapAt[cid].get(int(offset / Constants.kWordSize)):
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readWordWith32BitReads(snapshot.stream))
					else:
						#TODO: verify
						instancePtr['data'].append(StreamUtils.readRef(snapshot.stream))
					offset += Constants.kWordSize
				if offset < instanceSize:
					#TODO: verify
					instancePtr['data'].append(None)
				
				snapshot.references[refId] = instancePtr

	# Class ID: 44
	class TypeArgumentsDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('type args')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				isCanonical = StreamUtils.readBool(snapshot.stream)
				typeArgsPtr = { }
				typeArgsPtr['length'] = length
				typeArgsPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
				typeArgsPtr['nullability'] = StreamUtils.readUnsigned(snapshot.stream)
				typeArgsPtr['instantiations'] = StreamUtils.readRef(snapshot.stream)
				typeArgsPtr['types'] = []
				for j in range(length):
					typeArgsPtr['types'].append(StreamUtils.readRef(snapshot.stream))

				snapshot.references[refId] = typeArgsPtr

	# Class ID: 46
	class TypeDeserializer():
		def readAlloc(self, snapshot):
			self.canonicalStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type (canonical)')
			self.canonicalStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			# Canonicalization plays no role in parsing
			for refId in range(self.canonicalStartIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot)
				typePtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['typeState'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot):
			typePtr = { }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['typeClassId'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['arguments'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['signature'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr

	# Class ID: 47
	class TypeRefDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type refs')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				typePtr = { }
				typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
				typePtr['type'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = typePtr

	# Class ID: 48
	class TypeParameterDeserializer():
		def readAlloc(self, snapshot):
			self.canonicalStartIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type parameter (canonical)')
			self.canonicalStopIndex = snapshot.nextRefIndex

			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('type parameter')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			# Canonicalization plays no role in parsing
			for refId in range(self.canonicalStartIndex, self.stopIndex):
				typePtr = self._readFromTo(snapshot)
				typePtr['parametrizedClassId'] = StreamUtils.readInt(snapshot.stream, 32)
				typePtr['tokenPos'] = StreamUtils.readTokenPosition(snapshot.stream)
				typePtr['index'] = StreamUtils.readInt(snapshot.stream, 16)
				combined = StreamUtils.readUnsigned(snapshot.stream, 8)
				typePtr['flags'] = combined >> Constants.kNullabilityBitSize
				typePtr['nullability'] = combined & Constants.kNullabilityBitMask

				snapshot.references[refId] = typePtr

		def _readFromTo(self, snapshot):
			typePtr = { }
			typePtr['typeTestStub'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['name'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['bound'] = StreamUtils.readUnsigned(snapshot.stream)
			typePtr['parametrizedFunction'] = StreamUtils.readUnsigned(snapshot.stream)

			return typePtr


	# Class ID: 49
	class ClosureDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('closure')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				closurePtr = { }
				closurePtr['instantiatorTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['functionTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['delayedTypeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['function'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['context'] = StreamUtils.readUnsigned(snapshot.stream)
				closurePtr['hash'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = closurePtr

	# Class ID: 53
	class MintDeserializer():
		def readAlloc(self, snapshot):
			count = StreamUtils.readUnsigned(snapshot.stream)
			for i in range(count):
				StreamUtils.readBool(snapshot.stream)
				StreamUtils.readInt(snapshot.stream, 64)
				snapshot.assignRef('smi or uninitialized')

		def readFill(self, snapshot):
			return

	# Class ID: 54
	class DoubleDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('double')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				snapshot.references[refId] = { 'value': StreamUtils.readInt(snapshot.stream, 64)}

	# Class ID: 56
	class GrowableObjectArrayDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				snapshot.assignRef('growable object array')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				listPtr = { }
				listPtr['typeArguments'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['length'] = StreamUtils.readUnsigned(snapshot.stream)
				listPtr['data'] = StreamUtils.readUnsigned(snapshot.stream)

				snapshot.references[refId] = listPtr

	# Aggregate deserializer for class IDs: 78, 79
	class ArrayDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				StreamUtils.readUnsigned(snapshot.stream) # Length is read again during fill
				snapshot.assignRef('array')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				arrayPtr = { }
				arrayPtr['typeArguments'] = StreamUtils.readRef(snapshot.stream)
				arrayPtr['length'] = length
				arrayPtr['data'] = []
				for _ in range(length):
					arrayPtr['data'].append(StreamUtils.readRef(snapshot.stream))

				snapshot.references[refId] = arrayPtr

	# Class ID: 81
	class OneByteStringDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('one byte string')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				StreamUtils.readBool(snapshot.stream) # Canonicalization plays no role in parsing
				strPtr = { }
				strPtr['hash'] = StreamUtils.readInt(snapshot.stream, 32)
				strPtr['length'] = length
				strPtr['data'] = ''.join(chr(x) for x in snapshot.stream.read(length))

				snapshot.references[refId] = strPtr

	# Class ID: 82
	class TwoByteStringDeserializer():
		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('two-byte string')
			self.stopIndex = snapshot.nextRefIndex

	# Aggregate deserializer for class IDs: 108, 111, 114, 117, 120, 123, 126, 129, 132, 135, 138, 141, 144, 147
	class TypedDataDeserializer():
		def __init__(self, cid):
			self.elementSize = TypedData.elementSizeInBytes(cid)

		def readAlloc(self, snapshot):
			self.startIndex = snapshot.nextRefIndex
			count = StreamUtils.readUnsigned(snapshot.stream)
			for _ in range(count):
				length = StreamUtils.readUnsigned(snapshot.stream)
				snapshot.assignRef('typed data')
			self.stopIndex = snapshot.nextRefIndex

		def readFill(self, snapshot):
			for refId in range(self.startIndex, self.stopIndex):
				length = StreamUtils.readUnsigned(snapshot.stream)
				isCanonical = StreamUtils.readBool(snapshot.stream)
				lengthInBytes = length * self.elementSize
				dataPtr = { }
				dataPtr['length'] = length
				dataPtr['data'] = snapshot.stream.read(lengthInBytes)

				snapshot.references[refId] = dataPtr

	if cid >= ClassId.NUM_PREDEFINED.value or cid == ClassId.INSTANCE.value:
		return InstanceDeserializer(cid)

	if ClassId.isTypedDataViewClass(cid):
		raise Exception('Typed data view deserializer not implemented')

	if ClassId.isExternalTypedDataClass(cid):
		raise Exception('External typed data deserializer not implemented')

	if ClassId.isTypedDataClass(cid):
		return TypedDataDeserializer(cid)

	if includesCode:
		if ClassId(cid) is ClassId.PC_DESCRIPTORS or ClassId(cid) is ClassId.CODE_SOURCE_MAP or \
		ClassId(cid) is ClassId.COMPRESSED_STACK_MAPS or ClassId(cid) is ClassId.ONE_BYTE_STRING or \
		ClassId(cid) is ClassId.TWO_BYTE_STRING:
			return RODataDeserializer()

	if ClassId(cid) is ClassId.ILLEGAL:
		raise Exception('Encountered illegal cluster')
	if ClassId(cid) is ClassId.CLASS:
		return ClassDeserializer()
	if ClassId(cid) is ClassId.PATCH_CLASS:
		return PatchClassDeserializer()
	if ClassId(cid) is ClassId.FUNCTION:
		return FunctionDeserializer()
	if ClassId(cid) is ClassId.CLOSURE_DATA:
		return ClosureDataDeserializer()
	if ClassId(cid) is ClassId.SIGNATURE_DATA:
		return SignatureDataDeserializer()
	if ClassId(cid) is ClassId.FIELD:
		return FieldDeserializer()
	if ClassId(cid) is ClassId.SCRIPT:
		return ScriptDeserializer()
	if ClassId(cid) is ClassId.LIBRARY:
		return LibraryDeserializer()
	if ClassId(cid) is ClassId.CODE:
		return CodeDeserializer()
	if ClassId(cid) is ClassId.OBJECT_POOL:
		return ObjectPoolDeserializer()
	if ClassId(cid) is ClassId.PC_DESCRIPTORS:
		return PcDescriptorsDeserializer()
	if ClassId(cid) is ClassId.CODE_SOURCE_MAP:
		return RODataDeserializer()
	if ClassId(cid) is ClassId.COMPRESSED_STACK_MAPS:
		return RODataDeserializer()
	if ClassId(cid) is ClassId.EXCEPTION_HANDLERS:
		return ExceptionHandlersDeserializer()
	if ClassId(cid) is ClassId.UNLINKED_CALL:
		return UnlinkedCallDeserializer()
	if ClassId(cid) is ClassId.MEGAMORPHIC_CACHE:
		return MegamorphicCacheDeserializer()
	if ClassId(cid) is ClassId.SUBTYPE_TEST_CACHE:
		return SubtypeTestCacheDeserializer()
	if ClassId(cid) is ClassId.LOADING_UNIT:
		return LoadingUnitDeserializer()
	if ClassId(cid) is ClassId.TYPE_ARGUMENTS:
		return TypeArgumentsDeserializer()
	if ClassId(cid) is ClassId.TYPE:
		return TypeDeserializer()
	if ClassId(cid) is ClassId.TYPE_REF:
		return TypeRefDeserializer()
	if ClassId(cid) is ClassId.TYPE_PARAMETER:
		return TypeParameterDeserializer()
	if ClassId(cid) is ClassId.CLOSURE:
		return ClosureDeserializer()
	if ClassId(cid) is ClassId.MINT:
		return MintDeserializer()
	if ClassId(cid) is ClassId.DOUBLE:
		return DoubleDeserializer()
	if ClassId(cid) is ClassId.GROWABLE_OBJECT_ARRAY:
		return GrowableObjectArrayDeserializer()
	if ClassId(cid) is ClassId.ARRAY:
		return ArrayDeserializer()
	if ClassId(cid) is ClassId.IMMUTABLE_ARRAY:
		return ArrayDeserializer()
	if ClassId(cid) is ClassId.ONE_BYTE_STRING:
		return OneByteStringDeserializer()
	if ClassId(cid) is ClassId.TWO_BYTE_STRING:
		return TwoByteStringDeserializer()
	
	raise Exception('Deserializer missing for class {}'.format(ClassId(cid).name))