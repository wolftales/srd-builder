"""Canonical lineage data from SRD 5.1 PDF pages 3-7.

SOURCE: SRD_CC_v5.1.pdf pages 3-7 "Races" section
EXTRACTION: PDF text is corrupted; manually transcribed via visual inspection
PROVENANCE: Each lineage includes page number and section reference
"""

from typing import Final

# Lineage data structure
# Each lineage has: name, ability_modifiers, size, speed, traits, languages, page, subraces (optional)

LINEAGE_DATA: Final[list[dict]] = [
    {
        "name": "Dwarf",
        "simple_name": "dwarf",
        "page": 3,
        "ability_modifiers": {"constitution": 2},
        "size": "Medium",
        "speed": 25,
        "age": "Dwarves mature at the same rate as humans, but they're considered young until they reach the age of 50. On average, they live about 350 years.",
        "alignment": "Most dwarves are lawful, believing firmly in the benefits of a well-ordered society. They tend toward good as well, with a strong sense of fair play and a belief that everyone deserves to share in the benefits of a just order.",
        "size_description": "Dwarves stand between 4 and 5 feet tall and average about 150 pounds. Your size is Medium.",
        "languages": ["Common", "Dwarvish"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Dwarven Resilience",
                "text": "You have advantage on saving throws against poison, and you have resistance against poison damage.",
            },
            {
                "name": "Dwarven Combat Training",
                "text": "You have proficiency with the battleaxe, handaxe, light hammer, and warhammer.",
            },
            {
                "name": "Tool Proficiency",
                "text": "You gain proficiency with the artisan's tools of your choice: smith's tools, brewer's supplies, or mason's tools.",
            },
            {
                "name": "Stonecunning",
                "text": "Whenever you make an Intelligence (History) check related to the origin of stonework, you are considered proficient in the History skill and add double your proficiency bonus to the check, instead of your normal proficiency bonus.",
            },
        ],
        "subraces": [
            {
                "name": "Hill Dwarf",
                "simple_name": "hill_dwarf",
                "ability_modifiers": {"wisdom": 1},
                "traits": [
                    {
                        "name": "Dwarven Toughness",
                        "text": "Your hit point maximum increases by 1, and it increases by 1 every time you gain a level.",
                    }
                ],
            }
        ],
    },
    {
        "name": "Elf",
        "simple_name": "elf",
        "page": 4,
        "ability_modifiers": {"dexterity": 2},
        "size": "Medium",
        "speed": 30,
        "age": "Although elves reach physical maturity at about the same age as humans, the elven understanding of adulthood goes beyond physical growth to encompass worldly experience. An elf typically claims adulthood and an adult name around the age of 100 and can live to be 750 years old.",
        "alignment": "Elves love freedom, variety, and self-expression, so they lean strongly toward the gentler aspects of chaos. They value and protect others' freedom as well as their own, and they are more often good than not.",
        "size_description": "Elves range from under 5 to over 6 feet tall and have slender builds. Your size is Medium.",
        "languages": ["Common", "Elvish"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Accustomed to twilit forests and the night sky, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Keen Senses",
                "text": "You have proficiency in the Perception skill.",
            },
            {
                "name": "Fey Ancestry",
                "text": "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
            },
            {
                "name": "Trance",
                "text": "Elves don't need to sleep. Instead, they meditate deeply, remaining semiconscious, for 4 hours a day. (The Common word for such meditation is 'trance.') While meditating, you can dream after a fashion; such dreams are actually mental exercises that have become reflexive through years of practice. After resting in this way, you gain the same benefit that a human does from 8 hours of sleep.",
            },
        ],
        "subraces": [
            {
                "name": "High Elf",
                "simple_name": "high_elf",
                "ability_modifiers": {"intelligence": 1},
                "traits": [
                    {
                        "name": "Elf Weapon Training",
                        "text": "You have proficiency with the longsword, shortsword, shortbow, and longbow.",
                    },
                    {
                        "name": "Cantrip",
                        "text": "You know one cantrip of your choice from the wizard spell list. Intelligence is your spellcasting ability for it.",
                    },
                    {
                        "name": "Extra Language",
                        "text": "You can speak, read, and write one extra language of your choice.",
                    },
                ],
            }
        ],
    },
    {
        "name": "Halfling",
        "simple_name": "halfling",
        "page": 4,
        "ability_modifiers": {"dexterity": 2},
        "size": "Small",
        "speed": 25,
        "age": "A halfling reaches adulthood at the age of 20 and generally lives into the middle of his or her second century.",
        "alignment": "Most halflings are lawful good. As a rule, they are good-hearted and kind, hate to see others in pain, and have no tolerance for oppression. They are also very orderly and traditional, leaning heavily on the support of their community and the comfort of their old ways.",
        "size_description": "Halflings average about 3 feet tall and weigh about 40 pounds. Your size is Small.",
        "languages": ["Common", "Halfling"],
        "traits": [
            {
                "name": "Lucky",
                "text": "When you roll a 1 on the d20 for an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll.",
            },
            {
                "name": "Brave",
                "text": "You have advantage on saving throws against being frightened.",
            },
            {
                "name": "Halfling Nimbleness",
                "text": "You can move through the space of any creature that is of a size larger than yours.",
            },
        ],
        "subraces": [
            {
                "name": "Lightfoot Halfling",
                "simple_name": "lightfoot_halfling",
                "ability_modifiers": {"charisma": 1},
                "traits": [
                    {
                        "name": "Naturally Stealthy",
                        "text": "You can attempt to hide even when you are obscured only by a creature that is at least one size larger than you.",
                    }
                ],
            }
        ],
    },
    {
        "name": "Human",
        "simple_name": "human",
        "page": 5,
        "ability_modifiers": {
            "strength": 1,
            "dexterity": 1,
            "constitution": 1,
            "intelligence": 1,
            "wisdom": 1,
            "charisma": 1,
        },
        "size": "Medium",
        "speed": 30,
        "age": "Humans reach adulthood in their late teens and live less than a century.",
        "alignment": "Humans tend toward no particular alignment. The best and the worst are found among them.",
        "size_description": "Humans vary widely in height and build, from barely 5 feet to well over 6 feet tall. Regardless of your position in that range, your size is Medium.",
        "languages": ["Common", "one extra language of your choice"],
        "traits": [],  # Humans have no special traits beyond ability increases
        "subraces": [],
    },
    {
        "name": "Dragonborn",
        "simple_name": "dragonborn",
        "page": 5,
        "ability_modifiers": {"strength": 2, "charisma": 1},
        "size": "Medium",
        "speed": 30,
        "age": "Young dragonborn grow quickly. They walk hours after hatching, attain the size and development of a 10-year-old human child by the age of 3, and reach adulthood by 15. They live to be around 80.",
        "alignment": "Dragonborn tend to extremes, making a conscious choice for one side or the other in the cosmic war between good and evil. Most dragonborn are good, but those who side with evil can be terrible villains.",
        "size_description": "Dragonborn are taller and heavier than humans, standing well over 6 feet tall and averaging almost 250 pounds. Your size is Medium.",
        "languages": ["Common", "Draconic"],
        "traits": [
            {
                "name": "Draconic Ancestry",
                "text": "You have draconic ancestry. Choose one type of dragon from the Draconic Ancestry table. Your breath weapon and damage resistance are determined by the dragon type, as shown in the table.",
                "references_table": "draconic_ancestry",  # Custom table, not in v0.7.0
            },
            {
                "name": "Breath Weapon",
                "text": "You can use your action to exhale destructive energy. Your draconic ancestry determines the size, shape, and damage type of the exhalation. When you use your breath weapon, each creature in the area of the exhalation must make a saving throw, the type of which is determined by your draconic ancestry. The DC for this saving throw equals 8 + your Constitution modifier + your proficiency bonus. A creature takes 2d6 damage on a failed save, and half as much damage on a successful one. The damage increases to 3d6 at 6th level, 4d6 at 11th level, and 5d6 at 16th level. After you use your breath weapon, you can't use it again until you complete a short or long rest.",
            },
            {
                "name": "Damage Resistance",
                "text": "You have resistance to the damage type associated with your draconic ancestry.",
            },
        ],
        "subraces": [],
    },
    {
        "name": "Gnome",
        "simple_name": "gnome",
        "page": 6,
        "ability_modifiers": {"intelligence": 2},
        "size": "Small",
        "speed": 25,
        "age": "Gnomes mature at the same rate humans do, and most are expected to settle down into an adult life by around age 40. They can live 350 to almost 500 years.",
        "alignment": "Gnomes are most often good. Those who tend toward law are sages, engineers, researchers, scholars, investigators, or inventors. Those who tend toward chaos are minstrels, tricksters, wanderers, or fanciful jewelers. Gnomes are good-hearted, and even the tricksters among them are more playful than vicious.",
        "size_description": "Gnomes are between 3 and 4 feet tall and average about 40 pounds. Your size is Small.",
        "languages": ["Common", "Gnomish"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Gnome Cunning",
                "text": "You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic.",
            },
        ],
        "subraces": [
            {
                "name": "Rock Gnome",
                "simple_name": "rock_gnome",
                "ability_modifiers": {"constitution": 1},
                "traits": [
                    {
                        "name": "Artificer's Lore",
                        "text": "Whenever you make an Intelligence (History) check related to magic items, alchemical objects, or technological devices, you can add twice your proficiency bonus, instead of any proficiency bonus you normally apply.",
                    },
                    {
                        "name": "Tinker",
                        "text": "You have proficiency with artisan's tools (tinker's tools). Using those tools, you can spend 1 hour and 10 gp worth of materials to construct a Tiny clockwork device (AC 5, 1 hp). The device ceases to function after 24 hours (unless you spend 1 hour repairing it to keep the device functioning), or when you use your action to dismantle it; at that time, you can reclaim the materials used to create it. You can have up to three such devices active at a time. When you create a device, choose one of the following options: Clockwork Toy, Fire Starter, Music Box.",
                    },
                ],
            }
        ],
    },
    {
        "name": "Half-Elf",
        "simple_name": "half_elf",
        "page": 6,
        "ability_modifiers": {"charisma": 2, "other": 2},  # +2 to Cha, +1 to two others
        "ability_modifier_note": "Your Charisma score increases by 2, and two other ability scores of your choice increase by 1.",
        "size": "Medium",
        "speed": 30,
        "age": "Half-elves mature at the same rate humans do and reach adulthood around the age of 20. They live much longer than humans, however, often exceeding 180 years.",
        "alignment": "Half-elves share the chaotic bent of their elven heritage. They value both personal freedom and creative expression, demonstrating neither love of leaders nor desire for followers. They chafe at rules, resent others' demands, and sometimes prove unreliable, or at least unpredictable.",
        "size_description": "Half-elves are about the same size as humans, ranging from 5 to 6 feet tall. Your size is Medium.",
        "languages": ["Common", "Elvish", "one extra language of your choice"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Thanks to your elf blood, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Fey Ancestry",
                "text": "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
            },
            {
                "name": "Skill Versatility",
                "text": "You gain proficiency in two skills of your choice.",
            },
        ],
        "subraces": [],
    },
    {
        "name": "Half-Orc",
        "simple_name": "half_orc",
        "page": 7,
        "ability_modifiers": {"strength": 2, "constitution": 1},
        "size": "Medium",
        "speed": 30,
        "age": "Half-orcs mature a little faster than humans, reaching adulthood around age 14. They age noticeably faster and rarely live longer than 75 years.",
        "alignment": "Half-orcs inherit a tendency toward chaos from their orc parents and are not strongly inclined toward good. Half-orcs raised among orcs and willing to live out their lives among them are usually evil.",
        "size_description": "Half-orcs are somewhat larger and bulkier than humans, and they range from 5 to well over 6 feet tall. Your size is Medium.",
        "languages": ["Common", "Orc"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Thanks to your orc blood, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Menacing",
                "text": "You gain proficiency in the Intimidation skill.",
            },
            {
                "name": "Relentless Endurance",
                "text": "When you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. You can't use this feature again until you finish a long rest.",
            },
            {
                "name": "Savage Attacks",
                "text": "When you score a critical hit with a melee weapon attack, you can roll one of the weapon's damage dice one additional time and add it to the extra damage of the critical hit.",
            },
        ],
        "subraces": [],
    },
    {
        "name": "Tiefling",
        "simple_name": "tiefling",
        "page": 7,
        "ability_modifiers": {"intelligence": 1, "charisma": 2},
        "size": "Medium",
        "speed": 30,
        "age": "Tieflings mature at the same rate as humans but live a few years longer.",
        "alignment": "Tieflings might not have an innate tendency toward evil, but many of them end up there. Evil or not, an independent nature inclines many tieflings toward a chaotic alignment.",
        "size_description": "Tieflings are about the same size and build as humans. Your size is Medium.",
        "languages": ["Common", "Infernal"],
        "traits": [
            {
                "name": "Darkvision",
                "text": "Thanks to your infernal heritage, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            },
            {
                "name": "Hellish Resistance",
                "text": "You have resistance to fire damage.",
            },
            {
                "name": "Infernal Legacy",
                "text": "You know the thaumaturgy cantrip. When you reach 3rd level, you can cast the hellish rebuke spell as a 2nd-level spell once with this trait and regain the ability to do so when you finish a long rest. When you reach 5th level, you can cast the darkness spell once with this trait and regain the ability to do so when you finish a long rest. Charisma is your spellcasting ability for these spells.",
                "references_spells": ["thaumaturgy", "hellish_rebuke", "darkness"],
            },
        ],
        "subraces": [],
    },
]
