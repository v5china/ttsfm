# TTSFM Combined Audio Tests

This directory contains comprehensive tests for the new combined audio functionality in TTSFM.

## Test Structure

### Unit Tests

#### `test_combined_audio.py`
- **TestTextSplitting**: Tests the intelligent text splitting algorithm
- **TestAudioCombination**: Tests basic audio combination functionality
- **TestTTSResponseCombination**: Tests combining TTSResponse objects
- **TestErrorHandling**: Tests error handling scenarios
- **TestIntegrationScenarios**: Tests complete workflows
- **TestPerformanceScenarios**: Tests performance with large inputs

#### `test_audio_combination.py`
- **TestAudioCombinationDetailed**: Detailed tests for audio combination
- Tests PyDub integration with mocking
- Tests fallback mechanisms
- Tests different audio formats
- Tests error scenarios and recovery

### Integration Tests

#### `test_combined_endpoints.py`
- **TestCombinedAudioEndpoints**: Tests HTTP endpoints
- Tests both `/api/generate-combined` and `/v1/audio/speech-combined`
- Tests different voices, formats, and parameters
- Tests error handling and edge cases
- Tests performance with large texts
- Tests concurrent requests

## Running Tests

### Quick Test Run
```bash
# Run all tests with the test runner
python run_combined_audio_tests.py
```

### Individual Test Suites
```bash
# Unit tests only
python tests/test_combined_audio.py

# Audio combination tests only
python tests/test_audio_combination.py

# Integration tests only (requires server running)
python tests/test_combined_endpoints.py
```

### Manual Testing
```bash
# Test the actual endpoints manually
python test_combined_endpoint.py
```

## Prerequisites

### Required Dependencies
- `unittest` (built-in)
- `requests` (for integration tests)
- `ttsfm` package
- `flask` (for web server)

### Optional Dependencies
- `pydub` (for advanced audio processing)

### Server Requirements
For integration tests, the TTSFM web server must be running:
```bash
cd ttsfm-web
python app.py
```

## Test Categories

### 🧪 Unit Tests
- **Text Splitting Algorithm**
  - Sentence boundary detection
  - Word boundary preservation
  - Character-level fallback
  - Unicode text handling
  - Performance with large texts

- **Audio Combination Logic**
  - PyDub integration
  - WAV concatenation fallback
  - Format handling
  - Error recovery
  - Memory efficiency

- **Data Model Integration**
  - TTSResponse object handling
  - Metadata preservation
  - Format conversion

### 🌐 Integration Tests
- **HTTP Endpoint Testing**
  - Request/response validation
  - Header verification
  - Error response formats
  - Content-Type handling

- **API Compatibility**
  - Native TTSFM API format
  - OpenAI-compatible format
  - Parameter validation
  - Error message consistency

- **Real-world Scenarios**
  - Long text processing
  - Multiple format support
  - Concurrent request handling
  - Performance benchmarks

### 🔧 Manual Verification
- **End-to-end Functionality**
  - Actual audio generation
  - File saving and validation
  - Audio quality verification
  - Metadata accuracy

## Test Data

### Text Samples
- **Short Text**: Basic functionality testing
- **Long Text**: Splitting and combination testing
- **Unicode Text**: International character support
- **Edge Cases**: Empty text, single characters, very long words

### Audio Formats
- **MP3**: Most common format
- **WAV**: High quality, good for testing concatenation
- **OPUS**: Compressed format
- **AAC, FLAC, PCM**: Additional format coverage

### Voices
- **Primary**: alloy, nova, echo (most tested)
- **Secondary**: All 11 available voices
- **Error Cases**: Invalid voice names

## Expected Results

### Success Criteria
- ✅ All unit tests pass
- ✅ All integration tests pass (when server running)
- ✅ Manual verification succeeds
- ✅ No memory leaks or performance issues
- ✅ Proper error handling for all edge cases

### Performance Benchmarks
- **Text Splitting**: < 1 second for 50,000 characters
- **Audio Combination**: < 5 seconds for 10 chunks
- **End-to-end**: < 30 seconds for 5,000 character text
- **Memory Usage**: < 2x input size overhead

### Quality Metrics
- **Test Coverage**: > 90% of combined audio code
- **Error Handling**: All error paths tested
- **Format Support**: All 6 audio formats working
- **Voice Support**: All 11 voices working

## Troubleshooting

### Common Issues

#### "Server not running" errors
```bash
# Start the TTSFM web server
cd ttsfm-web
python app.py
```

#### Import errors
```bash
# Install missing dependencies
pip install requests pydub

# Install TTSFM package in development mode
pip install -e .
```

#### PyDub not available
```bash
# Install PyDub for advanced audio processing
pip install pydub

# Tests will still pass with fallback methods
```

#### Timeout errors
- Increase timeout values in test configuration
- Check server performance and load
- Verify network connectivity

### Test Debugging

#### Verbose Output
```bash
# Run with maximum verbosity
python -m unittest tests.test_combined_audio -v

# Run specific test class
python -m unittest tests.test_combined_audio.TestTextSplitting -v
```

#### Debug Mode
```bash
# Enable debug logging
export TTSFM_DEBUG=true
python run_combined_audio_tests.py
```

## Contributing

### Adding New Tests
1. Follow existing test patterns
2. Use descriptive test names
3. Include docstrings explaining test purpose
4. Test both success and failure cases
5. Add performance tests for new features

### Test Guidelines
- **Isolation**: Each test should be independent
- **Repeatability**: Tests should produce consistent results
- **Coverage**: Test all code paths and edge cases
- **Performance**: Include performance benchmarks
- **Documentation**: Clear test descriptions and comments

### Mock Usage
- Mock external dependencies (PyDub, network calls)
- Use realistic test data
- Test both mocked and real scenarios
- Verify mock interactions

## Test Results Interpretation

### Success Indicators
- All tests pass
- Performance within benchmarks
- No memory leaks
- Proper error handling
- Audio files generated successfully

### Warning Signs
- Intermittent test failures
- Performance degradation
- Memory usage spikes
- Audio quality issues
- Error handling gaps

### Failure Analysis
- Check server logs for errors
- Verify dependencies are installed
- Confirm test environment setup
- Review recent code changes
- Check for resource constraints
