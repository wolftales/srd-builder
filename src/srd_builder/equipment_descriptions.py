"""Equipment item descriptions extracted from SRD 5.1 pages 66-68.

This module provides prose descriptions for adventure gear items that have
special rules or require further explanation, as documented in the SRD.
"""

from typing import TypedDict


class ItemDescription(TypedDict):
    """Description data for an equipment item."""

    item_id: str  # References item in equipment.json
    description: str  # Full prose description from SRD
    page: int  # Source page


# Adventure Gear descriptions from SRD 5.1 pages 66-68
# Only items with special rules or mechanical descriptions
ADVENTURE_GEAR_DESCRIPTIONS: list[ItemDescription] = [
    {
        "item_id": "item:acid-vial",
        "description": "As an action, you can splash the contents of this vial onto a creature within 5 feet of you or throw the vial up to 20 feet, shattering it on impact. In either case, make a ranged attack against a creature or object, treating the acid as an improvised weapon. On a hit, the target takes 2d6 acid damage.",
        "page": 66,
    },
    {
        "item_id": "item:alchemists-fire-flask",
        "description": "This sticky, adhesive fluid ignites when exposed to air. As an action, you can throw this flask up to 20 feet, shattering it on impact. Make a ranged attack against a creature or object, treating the alchemist's fire as an improvised weapon. On a hit, the target takes 1d4 fire damage at the start of each of its turns. A creature can end this damage by using its action to make a DC 10 Dexterity check to extinguish the flames.",
        "page": 66,
    },
    {
        "item_id": "item:antitoxin-vial",
        "description": "A creature that drinks this vial of liquid gains advantage on saving throws against poison for 1 hour. It confers no benefit to undead or constructs.",
        "page": 67,
    },
    {
        "item_id": "item:arcane-focus",
        "description": "An arcane focus is a special item—an orb, a crystal, a rod, a specially constructed staff, a wand-like length of wood, or some similar item—designed to channel the power of arcane spells. A sorcerer, warlock, or wizard can use such an item as a spellcasting focus.",
        "page": 67,
    },
    {
        "item_id": "item:ball-bearings-bag-of-1000",
        "description": "As an action, you can spill these tiny metal balls from their pouch to cover a level, square area that is 10 feet on a side. A creature moving across the covered area must succeed on a DC 10 Dexterity saving throw or fall prone. A creature moving through the area at half speed doesn't need to make the save.",
        "page": 67,
    },
    {
        "item_id": "item:block-and-tackle",
        "description": "A set of pulleys with a cable threaded through them and a hook to attach to objects, a block and tackle allows you to hoist up to four times the weight you can normally lift.",
        "page": 67,
    },
    {
        "item_id": "item:book",
        "description": "A book might contain poetry, historical accounts, information pertaining to a particular field of lore, diagrams and notes on gnomish contraptions, or just about anything else that can be represented using text or pictures. A book of spells is a spellbook.",
        "page": 67,
    },
    {
        "item_id": "item:caltrops-bag-of-20",
        "description": "As an action, you can spread a bag of caltrops to cover a square area that is 5 feet on a side. Any creature that enters the area must succeed on a DC 15 Dexterity saving throw or stop moving this turn and take 1 piercing damage. Taking this damage reduces the creature's walking speed by 10 feet until the creature regains at least 1 hit point. A creature moving through the area at half speed doesn't need to make the save.",
        "page": 67,
    },
    {
        "item_id": "item:candle",
        "description": "For 1 hour, a candle sheds bright light in a 5-foot radius and dim light for an additional 5 feet.",
        "page": 67,
    },
    {
        "item_id": "item:case-crossbow-bolt",
        "description": "This wooden case can hold up to twenty crossbow bolts.",
        "page": 67,
    },
    {
        "item_id": "item:case-map-or-scroll",
        "description": "This cylindrical leather case can hold up to ten rolled-up sheets of paper or five rolled-up sheets of parchment.",
        "page": 67,
    },
    {
        "item_id": "item:chain-10-feet",
        "description": "A chain has 10 hit points. It can be burst with a successful DC 20 Strength check.",
        "page": 67,
    },
    {
        "item_id": "item:climbers-kit",
        "description": "A climber's kit includes special pitons, boot tips, gloves, and a harness. You can use the climber's kit as an action to anchor yourself; when you do, you can't fall more than 25 feet from the point where you anchored yourself, and you can't climb more than 25 feet away from that point without undoing the anchor.",
        "page": 67,
    },
    {
        "item_id": "item:component-pouch",
        "description": "A component pouch is a small, watertight leather belt pouch that has compartments to hold all the material components and other special items you need to cast your spells, except for those components that have a specific cost (as indicated in a spell's description).",
        "page": 67,
    },
    {
        "item_id": "item:crowbar",
        "description": "Using a crowbar grants advantage to Strength checks where the crowbar's leverage can be applied.",
        "page": 67,
    },
    {
        "item_id": "item:druidic-focus",
        "description": "A druidic focus might be a sprig of mistletoe or holly, a wand or scepter made of yew or another special wood, a staff drawn whole out of a living tree, or a totem object incorporating feathers, fur, bones, and teeth from sacred animals. A druid can use such an object as a spellcasting focus.",
        "page": 67,
    },
    {
        "item_id": "item:fishing-tackle",
        "description": "This kit includes a wooden rod, silken line, corkwood bobbers, steel hooks, lead sinkers, velvet lures, and narrow netting.",
        "page": 67,
    },
    {
        "item_id": "item:healers-kit",
        "description": "This kit is a leather pouch containing bandages, salves, and splints. The kit has ten uses. As an action, you can expend one use of the kit to stabilize a creature that has 0 hit points, without needing to make a Wisdom (Medicine) check.",
        "page": 67,
    },
    {
        "item_id": "item:holy-symbol",
        "description": "A holy symbol is a representation of a god or pantheon. It might be an amulet depicting a symbol representing a deity, the same symbol carefully engraved or inlaid as an emblem on a shield, or a tiny box holding a fragment of a sacred relic. A cleric or paladin can use a holy symbol as a spellcasting focus. To use the symbol in this way, the caster must hold it in hand, wear it visibly, or bear it on a shield.",
        "page": 67,
    },
    {
        "item_id": "item:holy-water-flask",
        "description": "As an action, you can splash the contents of this flask onto a creature within 5 feet of you or throw it up to 20 feet, shattering it on impact. In either case, make a ranged attack against a target creature, treating the holy water as an improvised weapon. If the target is a fiend or undead, it takes 2d6 radiant damage. A cleric or paladin may create holy water by performing a special ritual. The ritual takes 1 hour to perform, uses 25 gp worth of powdered silver, and requires the caster to expend a 1st-level spell slot.",
        "page": 67,
    },
    {
        "item_id": "item:hunting-trap",
        "description": "When you use your action to set it, this trap forms a saw-toothed steel ring that snaps shut when a creature steps on a pressure plate in the center. The trap is affixed by a heavy chain to an immobile object, such as a tree or a spike driven into the ground. A creature that steps on the plate must succeed on a DC 13 Dexterity saving throw or take 1d4 piercing damage and stop moving. Thereafter, until the creature breaks free of the trap, its movement is limited by the length of the chain (typically 3 feet long). A creature can use its action to make a DC 13 Strength check, freeing itself or another creature within its reach on a success. Each failed check deals 1 piercing damage to the trapped creature.",
        "page": 67,
    },
    {
        "item_id": "item:lamp",
        "description": "A lamp casts bright light in a 15-foot radius and dim light for an additional 30 feet. Once lit, it burns for 6 hours on a flask (1 pint) of oil.",
        "page": 68,
    },
    {
        "item_id": "item:lantern-bullseye",
        "description": "A bullseye lantern casts bright light in a 60-foot cone and dim light for an additional 60 feet. Once lit, it burns for 6 hours on a flask (1 pint) of oil.",
        "page": 68,
    },
    {
        "item_id": "item:lantern-hooded",
        "description": "A hooded lantern casts bright light in a 30-foot radius and dim light for an additional 30 feet. Once lit, it burns for 6 hours on a flask (1 pint) of oil. As an action, you can lower the hood, reducing the light to dim light in a 5-foot radius.",
        "page": 68,
    },
    {
        "item_id": "item:lock",
        "description": "A key is provided with the lock. Without the key, a creature proficient with thieves' tools can pick this lock with a successful DC 15 Dexterity check. Your GM may decide that better locks are available for higher prices.",
        "page": 68,
    },
    {
        "item_id": "item:magnifying-glass",
        "description": "This lens allows a closer look at small objects. It is also useful as a substitute for flint and steel when starting fires. Lighting a fire with a magnifying glass requires light as bright as sunlight to focus, tinder to ignite, and about 5 minutes for the fire to ignite. A magnifying glass grants advantage on any ability check made to appraise or inspect an item that is small or highly detailed.",
        "page": 68,
    },
    {
        "item_id": "item:manacles",
        "description": "These metal restraints can bind a Small or Medium creature. Escaping the manacles requires a successful DC 20 Dexterity check. Breaking them requires a successful DC 20 Strength check. Each set of manacles comes with one key. Without the key, a creature proficient with thieves' tools can pick the manacles' lock with a successful DC 15 Dexterity check. Manacles have 15 hit points.",
        "page": 68,
    },
    {
        "item_id": "item:mess-kit",
        "description": "This tin box contains a cup and simple cutlery. The box clamps together, and one side can be used as a cooking pan and the other as a plate or shallow bowl.",
        "page": 68,
    },
    {
        "item_id": "item:oil-flask",
        "description": "Oil usually comes in a clay flask that holds 1 pint. As an action, you can splash the oil in this flask onto a creature within 5 feet of you or throw it up to 20 feet, shattering it on impact. Make a ranged attack against a target creature or object, treating the oil as an improvised weapon. On a hit, the target is covered in oil. If the target takes any fire damage before the oil dries (after 1 minute), the target takes an additional 5 fire damage from the burning oil. You can also pour a flask of oil on the ground to cover a 5-foot-square area, provided that the surface is level. If lit, the oil burns for 2 rounds and deals 5 fire damage to any creature that enters the area or ends its turn in the area. A creature can take this damage only once per turn.",
        "page": 68,
    },
    {
        "item_id": "item:poison-basic-vial",
        "description": "You can use the poison in this vial to coat one slashing or piercing weapon or up to three pieces of ammunition. Applying the poison takes an action. A creature hit by the poisoned weapon or ammunition must make a DC 10 Constitution saving throw or take 1d4 poison damage. Once applied, the poison retains potency for 1 minute before drying.",
        "page": 68,
    },
    {
        "item_id": "item:potion-of-healing",
        "description": "A character who drinks the magical red fluid in this vial regains 2d4 + 2 hit points. Drinking or administering a potion takes an action.",
        "page": 68,
    },
    {
        "item_id": "item:pouch",
        "description": "A cloth or leather pouch can hold up to 20 sling bullets or 50 blowgun needles, among other things. A compartmentalized pouch for holding spell components is called a component pouch.",
        "page": 68,
    },
    {
        "item_id": "item:quiver",
        "description": "A quiver can hold up to 20 arrows.",
        "page": 68,
    },
    {
        "item_id": "item:ram-portable",
        "description": "You can use a portable ram to break down doors. When doing so, you gain a +4 bonus on the Strength check. One other character can help you use the ram, giving you advantage on this check.",
        "page": 68,
    },
    {
        "item_id": "item:rations-1-day",
        "description": "Rations consist of dry foods suitable for extended travel, including jerky, dried fruit, hardtack, and nuts.",
        "page": 68,
    },
    {
        "item_id": "item:rope-hempen-50-feet",
        "description": "Rope, whether made of hemp or silk, has 2 hit points and can be burst with a DC 17 Strength check.",
        "page": 68,
    },
    {
        "item_id": "item:scale-merchants",
        "description": "A scale includes a small balance, pans, and a suitable assortment of weights up to 2 pounds. With it, you can measure the exact weight of small objects, such as raw precious metals or trade goods, to help determine their worth.",
        "page": 68,
    },
    {
        "item_id": "item:spellbook",
        "description": "Essential for wizards, a spellbook is a leather-bound tome with 100 blank vellum pages suitable for recording spells.",
        "page": 68,
    },
    {
        "item_id": "item:spyglass",
        "description": "Objects viewed through a spyglass are magnified to twice their size.",
        "page": 68,
    },
    {
        "item_id": "item:tent",
        "description": "A simple and portable canvas shelter, a tent sleeps two.",
        "page": 68,
    },
    {
        "item_id": "item:tinderbox",
        "description": "This small container holds flint, fire steel, and tinder (usually dry cloth soaked in light oil) used to kindle a fire. Using it to light a torch—or anything else with abundant, exposed fuel—takes an action. Lighting any other fire takes 1 minute.",
        "page": 68,
    },
    {
        "item_id": "item:torch",
        "description": "A torch burns for 1 hour, providing bright light in a 20-foot radius and dim light for an additional 20 feet. If you make a melee attack with a burning torch and hit, it deals 1 fire damage.",
        "page": 68,
    },
]

# Tools descriptions from SRD 5.1 pages 70-71
TOOLS_DESCRIPTIONS: list[ItemDescription] = [
    {
        "item_id": "item:artisans-tools",
        "description": "These special tools include the items needed to pursue a craft or trade. Proficiency with a set of artisan's tools lets you add your proficiency bonus to any ability checks you make using the tools in your craft. Each type of artisan's tools requires a separate proficiency.",
        "page": 70,
    },
    {
        "item_id": "item:disguise-kit",
        "description": "This pouch of cosmetics, hair dye, and small props lets you create disguises that change your physical appearance. Proficiency with this kit lets you add your proficiency bonus to any ability checks you make to create a visual disguise.",
        "page": 71,
    },
    {
        "item_id": "item:forgery-kit",
        "description": "This small box contains a variety of papers and parchments, pens and inks, seals and sealing wax, gold and silver leaf, and other supplies necessary to create convincing forgeries of physical documents. Proficiency with this kit lets you add your proficiency bonus to any ability checks you make to create a physical forgery of a document.",
        "page": 71,
    },
    {
        "item_id": "item:gaming-set",
        "description": "This item encompasses a wide range of game pieces, including dice and decks of cards (for games such as Three-Dragon Ante). If you are proficient with a gaming set, you can add your proficiency bonus to ability checks you make to play a game with that set. Each type of gaming set requires a separate proficiency.",
        "page": 71,
    },
    {
        "item_id": "item:herbalism-kit",
        "description": "This kit contains a variety of instruments such as clippers, mortar and pestle, and pouches and vials used by herbalists to create remedies and potions. Proficiency with this kit lets you add your proficiency bonus to any ability checks you make to identify or apply herbs. Also, proficiency with this kit is required to create antitoxin and potions of healing.",
        "page": 71,
    },
    {
        "item_id": "item:musical-instrument",
        "description": "If you have proficiency with a given musical instrument, you can add your proficiency bonus to any ability checks you make to play music with the instrument. A bard can use a musical instrument as a spellcasting focus. Each type of musical instrument requires a separate proficiency.",
        "page": 71,
    },
    {
        "item_id": "item:navigators-tools",
        "description": "This set of instruments is used for navigation at sea. Proficiency with navigator's tools lets you chart a ship's course and follow navigation charts. In addition, these tools allow you to add your proficiency bonus to any ability check you make to avoid getting lost at sea.",
        "page": 71,
    },
    {
        "item_id": "item:poisoners-kit",
        "description": "A poisoner's kit includes the vials, chemicals, and other equipment necessary for the creation of poisons. Proficiency with this kit lets you add your proficiency bonus to any ability checks you make to craft or use poisons.",
        "page": 71,
    },
    {
        "item_id": "item:thieves-tools",
        "description": "This set of tools includes a small file, a set of lock picks, a small mirror mounted on a metal handle, a set of narrow-bladed scissors, and a pair of pliers. Proficiency with these tools lets you add your proficiency bonus to any ability checks you make to disarm traps or open locks.",
        "page": 71,
    },
]

# Armor descriptions from SRD 5.1 page 63
ARMOR_DESCRIPTIONS: list[ItemDescription] = [
    # Light Armor
    {
        "item_id": "item:padded",
        "description": "Padded armor consists of quilted layers of cloth and batting.",
        "page": 63,
    },
    {
        "item_id": "item:leather",
        "description": "The breastplate and shoulder protectors of this armor are made of leather that has been stiffened by being boiled in oil. The rest of the armor is made of softer and more flexible materials.",
        "page": 63,
    },
    {
        "item_id": "item:studded-leather",
        "description": "Made from tough but flexible leather, studded leather is reinforced with close-set rivets or spikes.",
        "page": 63,
    },
    # Medium Armor
    {
        "item_id": "item:hide",
        "description": "This crude armor consists of thick furs and pelts. It is commonly worn by barbarian tribes, evil humanoids, and other folk who lack access to the tools and materials needed to create better armor.",
        "page": 63,
    },
    {
        "item_id": "item:chain-shirt",
        "description": "Made of interlocking metal rings, a chain shirt is worn between layers of clothing or leather. This armor offers modest protection to the wearer's upper body and allows the sound of the rings rubbing against one another to be muffled by outer layers.",
        "page": 63,
    },
    {
        "item_id": "item:scale-mail",
        "description": "This armor consists of a coat and leggings (and perhaps a separate skirt) of leather covered with overlapping pieces of metal, much like the scales of a fish. The suit includes gauntlets.",
        "page": 63,
    },
    {
        "item_id": "item:breastplate",
        "description": "This armor consists of a fitted metal chest piece worn with supple leather. Although it leaves the legs and arms relatively unprotected, this armor provides good protection for the wearer's vital organs while leaving the wearer relatively unencumbered.",
        "page": 63,
    },
    {
        "item_id": "item:half-plate",
        "description": "Half plate consists of shaped metal plates that cover most of the wearer's body. It does not include leg protection beyond simple greaves that are attached with leather straps.",
        "page": 63,
    },
    # Heavy Armor
    {
        "item_id": "item:ring-mail",
        "description": "This armor is leather armor with heavy rings sewn into it. The rings help reinforce the armor against blows from swords and axes. Ring mail is inferior to chain mail, and it's usually worn only by those who can't afford better armor.",
        "page": 63,
    },
    {
        "item_id": "item:chain-mail",
        "description": "Made of interlocking metal rings, chain mail includes a layer of quilted fabric worn underneath the mail to prevent chafing and to cushion the impact of blows. The suit includes gauntlets.",
        "page": 63,
    },
    {
        "item_id": "item:splint",
        "description": "This armor is made of narrow vertical strips of metal riveted to a backing of leather that is worn over cloth padding. Flexible chain mail protects the joints.",
        "page": 63,
    },
    {
        "item_id": "item:plate",
        "description": "Plate consists of shaped, interlocking metal plates to cover the entire body. A suit of plate includes gauntlets, heavy leather boots, a visored helmet, and thick layers of padding underneath the armor. Buckles and straps distribute the weight over the body.",
        "page": 63,
    },
]

# Lifestyle descriptions from SRD 5.1 page 73
# Note: "Wretched" is described in prose but has no cost (not in tables)
# The other lifestyle levels map to consumable items (inn stay per day)
LIFESTYLE_DESCRIPTIONS: list[ItemDescription] = [
    {
        "item_id": "item:squalid",
        "description": "You live in a leaky stable, a mud-floored hut just outside town, or a vermin-infested boarding house in the worst part of town. You have shelter from the elements, but you live in a desperate and often violent environment, in places rife with disease, hunger, and misfortune. You are beneath the notice of most people, and you have few legal protections. Most people at this lifestyle level have suffered some terrible setback. They might be disturbed, marked as exiles, or suffer from disease.",
        "page": 73,
    },
    {
        "item_id": "item:poor",
        "description": "A poor lifestyle means going without the comforts available in a stable community. Simple food and lodgings, threadbare clothing, and unpredictable conditions result in a sufficient, though probably unpleasant, experience. Your accommodations might be a room in a flophouse or in the common room above a tavern. You benefit from some legal protections, but you still have to contend with violence, crime, and disease. People at this lifestyle level tend to be unskilled laborers, costermongers, peddlers, thieves, mercenaries, and other disreputable types.",
        "page": 73,
    },
    {
        "item_id": "item:modest",
        "description": "A modest lifestyle keeps you out of the slums and ensures that you can maintain your equipment. You live in an older part of town, renting a room in a boarding house, inn, or temple. You don't go hungry or thirsty, and your living conditions are clean, if simple. Ordinary people living modest lifestyles include soldiers with families, laborers, students, priests, hedge wizards, and the like.",
        "page": 73,
    },
    {
        "item_id": "item:comfortable",
        "description": "Choosing a comfortable lifestyle means that you can afford nicer clothing and can easily maintain your equipment. You live in a small cottage in a middle-class neighborhood or in a private room at a fine inn. You associate with merchants, skilled tradespeople, and military officers.",
        "page": 73,
    },
    {
        "item_id": "item:wealthy",
        "description": "Choosing a wealthy lifestyle means living a life of luxury, though you might not have achieved the social status associated with the old money of nobility or royalty. You live a lifestyle comparable to that of a highly successful merchant, a favored servant of the royalty, or the owner of a few small businesses. You have respectable lodgings, usually a spacious home in a good part of town or a comfortable suite at a fine inn. You likely have a small staff of servants.",
        "page": 73,
    },
    {
        "item_id": "item:aristocratic",
        "description": "You live a life of plenty and comfort. You move in circles populated by the most powerful people in the community. You have excellent lodgings, perhaps a townhouse in the nicest part of town or rooms in the finest inn. You dine at the best restaurants, retain the most skilled and fashionable tailor, and have servants attending to your every need. You receive invitations to the social gatherings of the rich and powerful, and spend evenings in the company of politicians, guild leaders, high priests, and nobility. You must also contend with the highest levels of deceit and treachery. The wealthier you are, the greater the chance you will be drawn into political intrigue as a pawn or participant.",
        "page": 73,
    },
]


def get_description_lookup() -> dict[str, str]:
    """Build lookup map of item_id to description.

    Returns:
        Dict mapping item_id → description text
    """
    all_descriptions = (
        ADVENTURE_GEAR_DESCRIPTIONS
        + TOOLS_DESCRIPTIONS
        + ARMOR_DESCRIPTIONS
        + LIFESTYLE_DESCRIPTIONS
    )
    return {item["item_id"]: item["description"] for item in all_descriptions}
