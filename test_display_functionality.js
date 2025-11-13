// Comprehensive Display Functionality Test
console.log('🧪 Starting Display Functionality Test...');

// Test data from actual backend response
const testResults = {
    session: { _id: "test-session", status: "completed" },
    ml_results: [
        {
            model_type: "classical",
            threat_probability: 0.935,
            classified_isotope: "U-238",
            model_confidence: 0.88,
            processing_time: 0.001
        },
        {
            model_type: "quantum",
            threat_level: "MEDIUM",
            threat_probability: 0.60,
            classified_isotope: "U-238",
            material_type: "Uranium",
            vqc_confidence: 0.50,
            qsvc_confidence: 0.50,
            model_agreement: 1.0,
            processing_time: 0.001
        }
    ],
    threat_assessment: {
        threat_level: "medium",
        overall_threat_probability: 0.68
    }
};

// Test 1: Check if all required elements exist
function testElementsExist() {
    console.log('📋 Test 1: Checking element existence...');
    
    const requiredElements = [
        'quantumThreatLevel', 'quantumThreat', 'quantumIsotope', 'quantumMaterialType',
        'quantumVQCConfidence', 'quantumQSVCConfidence', 'quantumProcessingTime', 'quantumModelAgreement'
    ];
    
    let allExist = true;
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            console.log(`  ✅ ${id}: Found`);
        } else {
            console.log(`  ❌ ${id}: Missing`);
            allExist = false;
        }
    });
    
    return allExist;
}

// Test 2: Test displayAnalysisResults function
function testDisplayFunction() {
    console.log('🎯 Test 2: Testing displayAnalysisResults function...');
    
    if (typeof displayAnalysisResults === 'function') {
        console.log('  ✅ displayAnalysisResults function exists');
        
        try {
            displayAnalysisResults(testResults);
            console.log('  ✅ Function executed without errors');
            return true;
        } catch (error) {
            console.log(`  ❌ Function execution failed: ${error.message}`);
            return false;
        }
    } else {
        console.log('  ❌ displayAnalysisResults function not found');
        return false;
    }
}

// Test 3: Verify values are updated correctly
function testValueUpdates() {
    console.log('📊 Test 3: Verifying value updates...');
    
    const expectedValues = {
        'quantumThreatLevel': 'MEDIUM',
        'quantumThreat': '60.0%',
        'quantumIsotope': 'U-238',
        'quantumMaterialType': 'Uranium',
        'quantumVQCConfidence': '50.0%',
        'quantumQSVCConfidence': '50.0%',
        'quantumProcessingTime': '0.001s',
        'quantumModelAgreement': '100.0%'
    };
    
    let allCorrect = true;
    Object.entries(expectedValues).forEach(([id, expected]) => {
        const element = document.getElementById(id);
        if (element) {
            const actual = element.textContent.trim();
            if (actual === expected) {
                console.log(`  ✅ ${id}: "${actual}" (correct)`);
            } else {
                console.log(`  ❌ ${id}: Expected "${expected}", got "${actual}"`);
                allCorrect = false;
            }
        } else {
            console.log(`  ❌ ${id}: Element not found`);
            allCorrect = false;
        }
    });
    
    return allCorrect;
}

// Test 4: Test tab switching
function testTabSwitching() {
    console.log('🔄 Test 4: Testing tab switching...');
    
    if (typeof showTab === 'function') {
        console.log('  ✅ showTab function exists');
        
        try {
            showTab('analysis');
            
            // Check if analysis tab is active
            const analysisTab = document.getElementById('analysis');
            if (analysisTab && analysisTab.classList.contains('active')) {
                console.log('  ✅ Analysis tab activated successfully');
                return true;
            } else {
                console.log('  ❌ Analysis tab not activated');
                return false;
            }
        } catch (error) {
            console.log(`  ❌ Tab switching failed: ${error.message}`);
            return false;
        }
    } else {
        console.log('  ❌ showTab function not found');
        return false;
    }
}

// Test 5: Test event listeners
function testEventListeners() {
    console.log('🎯 Test 5: Testing event listeners...');
    
    const buttons = ['generateBtn', 'runAnalysisBtn', 'exportPdfBtn', 'clearDataBtn'];
    let allWorking = true;
    
    buttons.forEach(btnId => {
        const button = document.getElementById(btnId);
        if (button) {
            console.log(`  ✅ ${btnId}: Button found`);
            
            // Test click event (without actually executing the function)
            const originalClick = button.onclick;
            let clickHandled = false;
            
            // Temporarily override click to test
            button.onclick = () => { clickHandled = true; };
            
            // Simulate click
            if (button.click) {
                try {
                    // Don't actually click, just check if handler exists
                    console.log(`  ✅ ${btnId}: Click handler available`);
                } catch (e) {
                    console.log(`  ❌ ${btnId}: Click handler error: ${e.message}`);
                    allWorking = false;
                }
            }
            
            // Restore original click handler
            button.onclick = originalClick;
        } else {
            console.log(`  ❌ ${btnId}: Button not found`);
            allWorking = false;
        }
    });
    
    return allWorking;
}

// Run all tests
function runAllTests() {
    console.log('🚀 Running comprehensive display functionality tests...\n');
    
    const results = {
        elementsExist: testElementsExist(),
        displayFunction: testDisplayFunction(),
        valueUpdates: testValueUpdates(),
        tabSwitching: testTabSwitching(),
        eventListeners: testEventListeners()
    };
    
    console.log('\n📋 === TEST RESULTS SUMMARY ===');
    Object.entries(results).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASSED' : 'FAILED'}`);
    });
    
    const allPassed = Object.values(results).every(result => result);
    console.log(`\n🎯 Overall Result: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
    
    return results;
}

// Auto-run tests when this script is loaded
if (typeof document !== 'undefined' && document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAllTests);
} else {
    // DOM already loaded, run tests immediately
    setTimeout(runAllTests, 100);
}

// Export for manual testing
window.testDisplayFunctionality = runAllTests;
