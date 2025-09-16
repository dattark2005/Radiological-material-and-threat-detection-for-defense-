from models.database import IsotopeReference
import logging

def initialize_isotope_database():
    """Initialize isotope reference database with common isotopes."""
    try:
        # Check if database is already populated
        from models.database import mongo
        if mongo.db.isotope_references.count_documents({}) > 0:
            return
        
        isotopes_data = [
            {
                'symbol': 'K-40',
                'name': 'Potassium-40',
                'atomic_number': 19,
                'mass_number': 40,
                'half_life': '1.25 billion years',
                'decay_mode': 'Beta decay, Electron capture',
                'gamma_peaks': [1460.8],
                'peak_intensities': [10.7],
                'isotope_type': 'Natural',
                'threat_level': 'Low',
                'description': 'Naturally occurring radioactive isotope of potassium found in soil, food, and the human body.',
                'common_uses': 'Geological dating, medical imaging',
                'safety_notes': 'Generally safe at natural levels. Part of normal background radiation.'
            },
            {
                'symbol': 'Cs-137',
                'name': 'Cesium-137',
                'atomic_number': 55,
                'mass_number': 137,
                'half_life': '30.17 years',
                'decay_mode': 'Beta decay',
                'gamma_peaks': [661.7],
                'peak_intensities': [85.1],
                'isotope_type': 'Medical',
                'threat_level': 'High',
                'description': 'Artificial radioisotope produced by nuclear fission, commonly used in medical and industrial applications.',
                'common_uses': 'Medical radiotherapy, industrial gauges, food irradiation',
                'safety_notes': 'Requires proper shielding and handling. Can cause radiation sickness at high doses.'
            },
            {
                'symbol': 'Co-60',
                'name': 'Cobalt-60',
                'atomic_number': 27,
                'mass_number': 60,
                'half_life': '5.27 years',
                'decay_mode': 'Beta decay',
                'gamma_peaks': [1173.2, 1332.5],
                'peak_intensities': [99.85, 99.98],
                'isotope_type': 'Industrial',
                'threat_level': 'High',
                'description': 'Artificial radioisotope used extensively in medical therapy and industrial applications.',
                'common_uses': 'Cancer radiotherapy, industrial radiography, sterilization',
                'safety_notes': 'Highly radioactive. Requires extensive shielding and remote handling equipment.'
            },
            {
                'symbol': 'U-238',
                'name': 'Uranium-238',
                'atomic_number': 92,
                'mass_number': 238,
                'half_life': '4.47 billion years',
                'decay_mode': 'Alpha decay',
                'gamma_peaks': [1001.0, 766.4, 63.3],
                'peak_intensities': [0.84, 0.29, 3.7],
                'isotope_type': 'Nuclear',
                'threat_level': 'Very High',
                'description': 'Naturally occurring uranium isotope, parent of the uranium decay series.',
                'common_uses': 'Nuclear fuel, depleted uranium applications, dating',
                'safety_notes': 'Radioactive and chemically toxic. Requires special nuclear material handling protocols.'
            },
            {
                'symbol': 'Ra-226',
                'name': 'Radium-226',
                'atomic_number': 88,
                'mass_number': 226,
                'half_life': '1600 years',
                'decay_mode': 'Alpha decay',
                'gamma_peaks': [186.2, 609.3, 351.9],
                'peak_intensities': [3.64, 45.5, 37.6],
                'isotope_type': 'Natural',
                'threat_level': 'High',
                'description': 'Naturally occurring radium isotope, part of uranium decay chain.',
                'common_uses': 'Historical medical treatments, luminous paints (discontinued)',
                'safety_notes': 'Highly radiotoxic. Accumulates in bones. Radon gas production hazard.'
            },
            {
                'symbol': 'Am-241',
                'name': 'Americium-241',
                'atomic_number': 95,
                'mass_number': 241,
                'half_life': '432.2 years',
                'decay_mode': 'Alpha decay',
                'gamma_peaks': [59.5, 26.3],
                'peak_intensities': [35.9, 2.4],
                'isotope_type': 'Industrial',
                'threat_level': 'High',
                'description': 'Artificial transuranic element used in smoke detectors and industrial applications.',
                'common_uses': 'Smoke detectors, industrial gauges, neutron sources',
                'safety_notes': 'Alpha emitter. Dangerous if ingested or inhaled. Requires careful handling.'
            },
            {
                'symbol': 'I-131',
                'name': 'Iodine-131',
                'atomic_number': 53,
                'mass_number': 131,
                'half_life': '8.02 days',
                'decay_mode': 'Beta decay',
                'gamma_peaks': [364.5, 636.9, 284.3],
                'peak_intensities': [81.7, 7.1, 6.1],
                'isotope_type': 'Medical',
                'threat_level': 'Medium',
                'description': 'Medical radioisotope used for thyroid treatments and imaging.',
                'common_uses': 'Thyroid cancer treatment, hyperthyroidism therapy, medical imaging',
                'safety_notes': 'Concentrates in thyroid gland. Requires isolation precautions during treatment.'
            },
            {
                'symbol': 'Tc-99m',
                'name': 'Technetium-99m',
                'atomic_number': 43,
                'mass_number': 99,
                'half_life': '6.01 hours',
                'decay_mode': 'Isomeric transition',
                'gamma_peaks': [140.5],
                'peak_intensities': [89.0],
                'isotope_type': 'Medical',
                'threat_level': 'Low',
                'description': 'Most widely used medical radioisotope for diagnostic imaging.',
                'common_uses': 'Medical imaging, SPECT scans, organ function studies',
                'safety_notes': 'Short half-life reduces radiation exposure. Standard medical radiation precautions apply.'
            },
            {
                'symbol': 'Sr-90',
                'name': 'Strontium-90',
                'atomic_number': 38,
                'mass_number': 90,
                'half_life': '28.9 years',
                'decay_mode': 'Beta decay',
                'gamma_peaks': [],  # Pure beta emitter
                'peak_intensities': [],
                'isotope_type': 'Nuclear',
                'threat_level': 'High',
                'description': 'Fission product with no significant gamma emissions, detected by beta radiation.',
                'common_uses': 'Radioisotope thermoelectric generators, medical applications',
                'safety_notes': 'Bone-seeking isotope. Dangerous if ingested. Pure beta emitter.'
            },
            {
                'symbol': 'Pu-239',
                'name': 'Plutonium-239',
                'atomic_number': 94,
                'mass_number': 239,
                'half_life': '24,110 years',
                'decay_mode': 'Alpha decay',
                'gamma_peaks': [129.3, 375.0, 413.7],
                'peak_intensities': [6.3, 1.5, 1.4],
                'isotope_type': 'Nuclear',
                'threat_level': 'Very High',
                'description': 'Fissile plutonium isotope used in nuclear weapons and reactors.',
                'common_uses': 'Nuclear weapons, nuclear reactor fuel, space missions',
                'safety_notes': 'Extremely dangerous. Special nuclear material requiring highest security measures.'
            }
        ]
        
        for isotope_data in isotopes_data:
            IsotopeReference.create(isotope_data)
        
        logging.info(f"Initialized isotope database with {len(isotopes_data)} isotopes")
        
    except Exception as e:
        logging.error(f"Failed to initialize isotope database: {str(e)}")
        raise
