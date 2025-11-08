# Table Discovery: Pages 60-75 (Equipment Chapter)

**Discovery Date:** 2025-11-04
**Method:** Manual review of SRD PDF
**PyMuPDF Auto-detection:** Found 1/15 tables (6.7% success rate)

## Discovered Tables

### Page 61: Suggested Characteristics (Acolyte Background)
- **Type:** Character background traits (5 sub-tables)
- **Category:** character_creation
- **Priority:** LOW
- **Notes:** Personality traits, ideals, bonds, flaws. PyMuPDF detected 1st entry of 1st table only.
- **Status:** Not extracted (low priority - flavor text)

### Page 62: Standard Exchange Rates
- **Type:** Currency conversion table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** Gold, silver, copper, electrum, platinum conversions
- **Status:** NOT DETECTED by PyMuPDF

### Page 63-64: Armor
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** HIGH
- **Notes:** AC, cost, weight, strength req, stealth disadvantage. Has preceding text descriptions.
- **Status:** NOT DETECTED by PyMuPDF
- **Action:** High-priority candidate for extraction

### Page 64: Donning and Doffing Armor
- **Type:** Time requirements table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** How long it takes to put on/remove armor
- **Status:** NOT DETECTED by PyMuPDF

### Page 65-66: Weapons
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** HIGH
- **Notes:** Damage, cost, weight, properties. Has preceding text descriptions.
- **Status:** NOT DETECTED by PyMuPDF
- **Action:** High-priority candidate for extraction

### Page 68-69: Adventure Gear
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** General adventuring equipment with costs/weights. Has preceding text descriptions.
- **Status:** NOT DETECTED by PyMuPDF

### Page 69-70: Container Capacity
- **Type:** Reference table
- **Category:** equipment
- **Priority:** LOW
- **Notes:** How much fits in backpacks, barrels, etc.
- **Status:** NOT DETECTED by PyMuPDF

### Page 70: Equipment Packs
- **Type:** Text descriptions (not true table)
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Burglar's pack, diplomat's pack, etc. Text format, not tabular.
- **Status:** NOT DETECTED (not a table)
- **Action:** Skip - better suited for equipment.json

### Page 70: Tools (Artisan Tools)
- **Type:** Text descriptions (not true table)
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Describes tool types. Text format, not tabular.
- **Status:** NOT DETECTED (not a table)
- **Action:** Skip - better suited for equipment.json

### Page 71-72: Mounts and Other Animals
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** Animal costs, speeds, carrying capacity
- **Status:** NOT DETECTED by PyMuPDF

### Page 72: Tack, Harness, and Drawn Vehicles
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Vehicle and animal equipment costs
- **Status:** NOT DETECTED by PyMuPDF

### Page 72: Waterborne Vehicles
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Ship/boat costs and speeds
- **Status:** NOT DETECTED by PyMuPDF

### Page 72: Trade Goods
- **Type:** Equipment reference table
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Commodity costs (wheat, iron, etc.)
- **Status:** NOT DETECTED by PyMuPDF

### Page 72-73: Lifestyle Expenses
- **Type:** Reference table with text descriptions
- **Category:** equipment
- **Priority:** LOW
- **Notes:** Daily living costs (wretched to aristocratic). Has preceding text descriptions.
- **Status:** NOT DETECTED by PyMuPDF
- **Currently:** EXTRACTED (in table_targets.py)

### Page 73-74: Food, Drink and Lodging
- **Type:** Reference table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** Inn/tavern costs
- **Status:** NOT DETECTED by PyMuPDF
- **Currently:** EXTRACTED (in table_targets.py)

### Page 74: Services
- **Type:** Reference table
- **Category:** equipment
- **Priority:** MEDIUM
- **Notes:** Hireling and service costs
- **Status:** NOT DETECTED by PyMuPDF
- **Currently:** EXTRACTED (in table_targets.py)

## Summary

**Total tables identified:** 15 (3 already extracted)
**PyMuPDF detection rate:** 1/15 (6.7%)
**Text-embedded tables:** 14/15 (93.3%)

**High-priority candidates for extraction:**
1. Armor (pg 63-64)
2. Weapons (pg 65-66)

**Medium-priority candidates:**
3. Standard Exchange Rates (pg 62)
4. Donning and Doffing Armor (pg 64)
5. Adventure Gear (pg 68-69)
6. Mounts and Other Animals (pg 71-72)

**Key Insight:** Equipment tables have preceding text descriptions of individual items. Tables provide quick reference summary data. This makes them challenging for auto-detection but valuable for users.

**Next Steps:**
1. Add high-priority tables (armor, weapons) to table_targets.py
2. Extract from PDF manually (text-embedded format)
3. Add to REFERENCE_TABLES in reference_data.py
4. Consider medium-priority tables for future iterations
