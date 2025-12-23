"""Parse skills dataset.

This module provides the 18 D&D 5e skills as static data.
No PDF extraction is required - these are game constants.

Source: SRD pages 76-79 (skill descriptions in "Using Ability Scores" chapter)
"""

from __future__ import annotations

__all__ = ["parse_skills"]

# The 18 D&D 5e skills from SRD pages 76-79
SKILLS_DATA = [
    {
        "id": "skill:acrobatics",
        "simple_name": "acrobatics",
        "name": "Acrobatics",
        "ability": "dexterity",
        "ability_id": "ability:dexterity",
        "description": [
            "Your Dexterity (Acrobatics) check covers your attempt to stay on your feet in a tricky situation, such as when you're trying to run across a sheet of ice, balance on a tightrope, or stay upright on a rocking ship's deck. The GM might also call for a Dexterity (Acrobatics) check to see if you can perform acrobatic stunts, including dives, rolls, somersaults, and flips."
        ],
        "page": 77,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:animal_handling",
        "simple_name": "animal_handling",
        "name": "Animal Handling",
        "ability": "wisdom",
        "ability_id": "ability:wisdom",
        "description": [
            "When there is any question whether you can calm down a domesticated animal, keep a mount from getting spooked, or intuit an animal's intentions, the GM might call for a Wisdom (Animal Handling) check. You also make a Wisdom (Animal Handling) check to control your mount when you attempt a risky maneuver."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:arcana",
        "simple_name": "arcana",
        "name": "Arcana",
        "ability": "intelligence",
        "ability_id": "ability:intelligence",
        "description": [
            "Your Intelligence (Arcana) check measures your ability to recall lore about spells, magic items, eldritch symbols, magical traditions, the planes of existence, and the inhabitants of those planes."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:athletics",
        "simple_name": "athletics",
        "name": "Athletics",
        "ability": "strength",
        "ability_id": "ability:strength",
        "description": [
            "Your Strength (Athletics) check covers difficult situations you encounter while climbing, jumping, or swimming. Examples include the following activities:",
            "• You attempt to climb a sheer or slippery cliff, avoid hazards while scaling a wall, or cling to a surface while something is trying to knock you off.",
            "• You try to jump an unusually long distance or pull off a stunt midjump.",
            "• You struggle to swim or stay afloat in treacherous currents, storm-tossed waves, or areas of thick seaweed. Or another creature tries to push or pull you underwater or otherwise interfere with your swimming.",
        ],
        "page": 76,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:deception",
        "simple_name": "deception",
        "name": "Deception",
        "ability": "charisma",
        "ability_id": "ability:charisma",
        "description": [
            "Your Charisma (Deception) check determines whether you can convincingly hide the truth, either verbally or through your actions. This deception can encompass everything from misleading others through ambiguity to telling outright lies. Typical situations include trying to fast-talk a guard, con a merchant, earn money through gambling, pass yourself off in a disguise, dull someone's suspicions with false assurances, or maintain a straight face while telling a blatant lie."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:history",
        "simple_name": "history",
        "name": "History",
        "ability": "intelligence",
        "ability_id": "ability:intelligence",
        "description": [
            "Your Intelligence (History) check measures your ability to recall lore about historical events, legendary people, ancient kingdoms, past disputes, recent wars, and lost civilizations."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:insight",
        "simple_name": "insight",
        "name": "Insight",
        "ability": "wisdom",
        "ability_id": "ability:wisdom",
        "description": [
            "Your Wisdom (Insight) check decides whether you can determine the true intentions of a creature, such as when searching out a lie or predicting someone's next move. Doing so involves gleaning clues from body language, speech habits, and changes in mannerisms."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:intimidation",
        "simple_name": "intimidation",
        "name": "Intimidation",
        "ability": "charisma",
        "ability_id": "ability:charisma",
        "description": [
            "When you attempt to influence someone through overt threats, hostile actions, and physical violence, the GM might ask you to make a Charisma (Intimidation) check. Examples include trying to pry information out of a prisoner, convincing street thugs to back down from a confrontation, or using the edge of a broken bottle to convince a sneering vizier to reconsider a decision."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:investigation",
        "simple_name": "investigation",
        "name": "Investigation",
        "ability": "intelligence",
        "ability_id": "ability:intelligence",
        "description": [
            "When you look around for clues and make deductions based on those clues, you make an Intelligence (Investigation) check. You might deduce the location of a hidden object, discern from the appearance of a wound what kind of weapon dealt it, or determine the weakest point in a tunnel that could cause it to collapse. Poring through ancient scrolls in search of a hidden fragment of knowledge might also call for an Intelligence (Investigation) check."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:medicine",
        "simple_name": "medicine",
        "name": "Medicine",
        "ability": "wisdom",
        "ability_id": "ability:wisdom",
        "description": [
            "A Wisdom (Medicine) check lets you try to stabilize a dying companion or diagnose an illness."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:nature",
        "simple_name": "nature",
        "name": "Nature",
        "ability": "intelligence",
        "ability_id": "ability:intelligence",
        "description": [
            "Your Intelligence (Nature) check measures your ability to recall lore about terrain, plants and animals, the weather, and natural cycles."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:perception",
        "simple_name": "perception",
        "name": "Perception",
        "ability": "wisdom",
        "ability_id": "ability:wisdom",
        "description": [
            "Your Wisdom (Perception) check lets you spot, hear, or otherwise detect the presence of something. It measures your general awareness of your surroundings and the keenness of your senses. For example, you might try to hear a conversation through a closed door, eavesdrop under an open window, or hear monsters moving stealthily in the forest. Or you might try to spot things that are obscured or easy to miss, whether they are orcs lying in ambush on a road, thugs hiding in the shadows of an alley, or candlelight under a closed secret door."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:performance",
        "simple_name": "performance",
        "name": "Performance",
        "ability": "charisma",
        "ability_id": "ability:charisma",
        "description": [
            "Your Charisma (Performance) check determines how well you can delight an audience with music, dance, acting, storytelling, or some other form of entertainment."
        ],
        "page": 79,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:persuasion",
        "simple_name": "persuasion",
        "name": "Persuasion",
        "ability": "charisma",
        "ability_id": "ability:charisma",
        "description": [
            "When you attempt to influence someone or a group of people with tact, social graces, or good nature, the GM might ask you to make a Charisma (Persuasion) check. Typically, you use persuasion when acting in good faith, to foster friendships, make cordial requests, or exhibit proper etiquette. Examples of persuading others include convincing a chamberlain to let your party see the king, negotiating peace between warring tribes, or inspiring a crowd of townsfolk."
        ],
        "page": 79,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:religion",
        "simple_name": "religion",
        "name": "Religion",
        "ability": "intelligence",
        "ability_id": "ability:intelligence",
        "description": [
            "Your Intelligence (Religion) check measures your ability to recall lore about deities, rites and prayers, religious hierarchies, holy symbols, and the practices of secret cults."
        ],
        "page": 78,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:sleight_of_hand",
        "simple_name": "sleight_of_hand",
        "name": "Sleight of Hand",
        "ability": "dexterity",
        "ability_id": "ability:dexterity",
        "description": [
            "Whenever you attempt an act of legerdemain or manual trickery, such as planting something on someone else or concealing an object on your person, make a Dexterity (Sleight of Hand) check. The GM might also call for a Dexterity (Sleight of Hand) check to determine whether you can lift a coin purse off another person or slip something out of another person's pocket."
        ],
        "page": 77,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:stealth",
        "simple_name": "stealth",
        "name": "Stealth",
        "ability": "dexterity",
        "ability_id": "ability:dexterity",
        "description": [
            "Make a Dexterity (Stealth) check when you attempt to conceal yourself from enemies, slink past guards, slip away without being noticed, or sneak up on someone without being seen or heard."
        ],
        "page": 77,
        "source": "SRD_CC_v5.1",
    },
    {
        "id": "skill:survival",
        "simple_name": "survival",
        "name": "Survival",
        "ability": "wisdom",
        "ability_id": "ability:wisdom",
        "description": [
            "The GM might ask you to make a Wisdom (Survival) check to follow tracks, hunt wild game, guide your group through frozen wastelands, identify signs that owlbears live nearby, predict the weather, or avoid quicksand and other natural hazards."
        ],
        "page": 79,
        "source": "SRD_CC_v5.1",
    },
]


def parse_skills() -> list[dict]:
    """Parse skills dataset.

    Returns:
        List of 18 skill records

    Note:
        This returns static data - the 18 D&D 5e skills are game constants.
        Descriptions are from SRD "Using Ability Scores" chapter (pages 76-79).
    """
    # Return a copy to prevent mutation
    return [dict(skill) for skill in SKILLS_DATA]
