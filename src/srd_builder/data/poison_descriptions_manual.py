"""Manual poison descriptions.

KNOWN LIMITATION: The SRD PDF has corrupted text on pages 204-205 where poison
descriptions are located. Text extraction returns garbled characters instead of
readable text. These descriptions were manually transcribed as a temporary solution.

TODO: Replace with automated extraction when a better PDF source is available.
"""

POISON_DESCRIPTIONS = {
    "assassin's_blood": {  # Note: Uses fancy apostrophe from PDF
        "description": "A creature subjected to this poison must make a DC 10 Constitution saving throw. On a failed save, it takes 6 (1d12) poison damage and is poisoned for 24 hours. On a successful save, the creature takes half damage and isn't poisoned.",
        "save": {"dc": 10, "ability": "constitution"},
        "damage": {
            "average": 6,
            "formula": "1d12",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "burnt_othur_fumes": {
        "description": "A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or take 10 (3d6) poison damage, and must repeat the saving throw at the start of each of its turns. On each successive failed save, the character takes 3 (1d6) poison damage. After three successful saves, the poison ends.",
        "save": {"dc": 13, "ability": "constitution"},
        "damage": {
            "average": 10,
            "formula": "3d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "crawler_mucus": {
        "description": "This poison must be harvested from a dead or incapacitated crawler. A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or be poisoned for 1 minute. The poisoned creature is paralyzed. The creature can repeat the saving throw at the end of each of its turns, ending the effect on itself on a success.",
        "save": {"dc": 13, "ability": "constitution"},
    },
    "drow_poison": {
        "description": "This poison is typically made only by the drow, and only in a place far removed from sunlight. A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or be poisoned for 1 hour. If the saving throw fails by 5 or more, the creature is also unconscious while poisoned in this way. The creature wakes up if it takes damage or if another creature takes an action to shake it awake.",
        "save": {"dc": 13, "ability": "constitution"},
    },
    "essence_of_ether": {
        "description": "A creature subjected to this poison must succeed on a DC 15 Constitution saving throw or become poisoned for 8 hours. The poisoned creature is unconscious. The creature wakes up if it takes damage or if another creature takes an action to shake it awake.",
        "save": {"dc": 15, "ability": "constitution"},
    },
    "malice": {
        "description": "A creature subjected to this poison must succeed on a DC 15 Constitution saving throw or become poisoned for 1 hour. The poisoned creature is blinded.",
        "save": {"dc": 15, "ability": "constitution"},
    },
    "midnight_tears": {
        "description": "A creature that ingests this poison suffers no effect until the stroke of midnight. If the poison has not been neutralized before then, the creature must succeed on a DC 17 Constitution saving throw, taking 31 (9d6) poison damage on a failed save, or half as much damage on a successful one.",
        "save": {"dc": 17, "ability": "constitution"},
        "damage": {
            "average": 31,
            "formula": "9d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "oil_of_taggit": {
        "description": "A creature subjected to this poison must succeed on a DC 13 Constitution saving throw or become poisoned for 24 hours. The poisoned creature is unconscious. The creature wakes up if it takes damage.",
        "save": {"dc": 13, "ability": "constitution"},
    },
    "pale_tincture": {
        "description": "A creature subjected to this poison must succeed on a DC 16 Constitution saving throw or take 3 (1d6) poison damage and become poisoned. The poisoned creature must repeat the saving throw every 24 hours, taking 3 (1d6) poison damage on a failed save. Until this poison ends, the damage the poison deals can't be healed by any means. After seven successful saving throws, the effect ends and the creature can heal normally.",
        "save": {"dc": 16, "ability": "constitution"},
        "damage": {
            "average": 3,
            "formula": "1d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "purple_worm_poison": {
        "description": "This poison must be harvested from a dead or incapacitated purple worm. A creature subjected to this poison must make a DC 19 Constitution saving throw, taking 42 (12d6) poison damage on a failed save, or half as much damage on a successful one.",
        "save": {"dc": 19, "ability": "constitution"},
        "damage": {
            "average": 42,
            "formula": "12d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "serpent_venom": {
        "description": "This poison must be harvested from a dead or incapacitated giant poisonous snake. A creature subjected to this poison must succeed on a DC 11 Constitution saving throw, taking 10 (3d6) poison damage on a failed save, or half as much damage on a successful one.",
        "save": {"dc": 11, "ability": "constitution"},
        "damage": {
            "average": 10,
            "formula": "3d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
    "torpor": {
        "description": "A creature subjected to this poison must succeed on a DC 15 Constitution saving throw or become poisoned for 4d6 hours. The poisoned creature is incapacitated.",
        "save": {"dc": 15, "ability": "constitution"},
    },
    "truth_serum": {
        "description": "A creature subjected to this poison must succeed on a DC 11 Constitution saving throw or become poisoned for 1 hour. The poisoned creature can't knowingly speak a lie, as if under the effect of a zone of truth spell.",
        "save": {"dc": 11, "ability": "constitution"},
    },
    "wyvern_poison": {
        "description": "This poison must be harvested from a dead or incapacitated wyvern. A creature subjected to this poison must make a DC 15 Constitution saving throw, taking 24 (7d6) poison damage on a failed save, or half as much damage on a successful one.",
        "save": {"dc": 15, "ability": "constitution"},
        "damage": {
            "average": 24,
            "formula": "7d6",
            "type": "poison",
            "type_id": "damage:poison",
        },
    },
}
