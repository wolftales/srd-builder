# Conditions Dataset Notes

Notes for implementing the conditions dataset (planned for v0.10.0).

## Spells That Apply/Modify Conditions

Found during v0.8.5 healing implementation:

### Spells That Grant Buffs (Positive Conditions)
- **Beacon of Hope** (3rd level, Cleric/Paladin)
  - Grants advantage on Wisdom saving throws
  - Grants advantage on death saving throws
  - Maximizes healing received (regain maximum HP possible from any healing)
  - Duration: Concentration, up to 1 minute

### Spells That Apply Debuffs (Negative Conditions)
- **Chill Touch** (Cantrip, Wizard/Sorcerer/Warlock)
  - Prevents target from regaining hit points
  - Duration: Until start of caster's next turn
  - Note: Despite name, does necrotic damage, not cold

## Implementation Notes

When building conditions dataset:
1. **Condition effects that modify healing:**
   - Beacon of Hope → "maximize_healing" buff
   - Chill Touch → "no_healing" debuff

2. **Consider extracting condition application from spells:**
   - Many spells apply standard conditions (Stunned, Paralyzed, Charmed, etc.)
   - Could cross-reference spell → condition relationships

3. **Condition categories:**
   - Standard conditions (PHB Appendix A): Blinded, Charmed, Deafened, etc.
   - Spell-specific buffs/debuffs: Beacon of Hope, Chill Touch, Bless, etc.
   - May want to separate "conditions" (standard) from "effects" (spell-specific)

## Related Work
- v0.8.5: Healing extraction complete, found these condition-like effects
- v0.10.0: Conditions dataset planned
