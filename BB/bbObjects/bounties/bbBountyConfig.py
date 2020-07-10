import random
from datetime import datetime, timedelta

from ...bbConfig import bbData, bbConfig
from ... import bbUtil
from ..items import bbShip

class BountyConfig:
    def __init__(self, faction="", name="", isPlayer=None, route=[], start="", end="", answer="", checked={}, reward=-1, issueTime=-1.0, endTime=-1.0, icon="", aliases=[], wiki="", activeShip=None, techLevel=-1):
        self.faction = faction.lower()
        self.name = name.title()
        self.isPlayer = False if isPlayer is None else isPlayer
        self.route = []
        for system in route:
            self.route.append(system.title())

        self.start = start.title()
        self.end = end.title()
        self.answer = answer.title()
        self.checked = checked
        self.reward = reward
        if type(reward) == float:
            self.reward = int(reward)
        self.issueTime = issueTime
        self.endTime = endTime
        self.icon = icon
        self.generated = False
        self.builtIn = False

        self.aliases = aliases
        self.wiki = wiki

        self.activeShip = activeShip
        self.techLevel = techLevel
        
    
    def generate(self, bountyDB, noCriminal=True, forceKeepChecked=False, forceNoDBCheck=False):
        doDBCheck = not forceNoDBCheck
        if noCriminal:
            if self.name in bbData.bountyNames:
                self.builtIn = True
            else:
                if self.faction == "":
                    self.faction = random.choice(bbData.bountyFactions)
                    while doDBCheck and not bountyDB.factionCanMakeBounty(self.faction):
                        self.faction = random.choice(bbData.bountyFactions)

                else:
                    if self.faction not in bbData.bountyFactions:
                        raise ValueError("BOUCONF_CONS_INVFAC: Invalid faction requested '" + self.faction + "'")
                    if doDBCheck and not bountyDB.factionCanMakeBounty(self.faction):
                        raise IndexError("BOUCONF_CONS_FACDBFULL: Attempted to generate new bounty config when no slots are available for faction: '" + self.faction + "'")

                if self.name == "":
                    self.builtIn = True
                    self.name = random.choice(bbData.bountyNames[self.faction])
                    while doDBCheck and bountyDB.bountyNameExists(self.name):
                        self.name = random.choice(bbData.bountyNames[self.faction])
                else:
                    if doDBCheck and bountyDB.bountyNameExists(self.name):
                        raise KeyError("BountyConfig: attempted to create config for pre-existing bounty: " + self.name)
                    
                    if self.icon == "":
                        self.icon = bbData.rocketIcon
        
        else:
            if doDBCheck and not bountyDB.factionCanMakeBounty(self.faction):
                raise IndexError("BOUCONF_CONS_FACDBFULL: Attempted to generate new bounty config when no slots are available for faction: '" + self.faction + "'")
        
        if self.techLevel == -1:
            self.techLevel = bbConfig.pickRandomCriminalTL()
        print("GENERATE LEVEL",self.techLevel)

        if self.route == []:
            if self.start == "":
                self.start = random.choice(list(bbData.builtInSystemObjs.keys()))
                while self.start == self.end or not bbData.builtInSystemObjs[self.start].hasJumpGate():
                    self.start = random.choice(list(bbData.builtInSystemObjs.keys()))
            elif self.start not in bbData.builtInSystemObjs:
                raise KeyError("BountyConfig: Invalid start system requested '" + self.start + "'")
            if self.end == "":
                self.end = random.choice(list(bbData.builtInSystemObjs.keys()))
                while self.start == self.end or not bbData.builtInSystemObjs[self.end].hasJumpGate():
                    self.end = random.choice(list(bbData.builtInSystemObjs.keys()))
            elif self.end not in bbData.builtInSystemObjs:
                raise KeyError("BountyConfig: Invalid end system requested '" + self.end + "'")
            # self.route = makeRoute(self.start, self.end)
            self.route = bbUtil.bbAStar(self.start, self.end, bbData.builtInSystemObjs)
        else:
            for system in self.route:
                if system not in bbData.builtInSystemObjs:
                    raise KeyError("BountyConfig: Invalid system in route '" + system + "'")
        if self.answer == "":
            self.answer = random.choice(self.route)
        elif self.answer not in bbData.builtInSystemObjs:
            raise KeyError("Bounty constructor: Invalid answer requested '" + self.answer + "'")

        if self.activeShip is None:
            if self.isPlayer:
                raise ValueError("Attempted to generate a player bounty without providing the activeShip")
            
            shipHasPrimary = False
            while not shipHasPrimary:
                shipTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                while len(bbData.shipKeysByTL[shipTL]) == 0:
                    shipTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                
                self.activeShip = bbShip.fromDict(bbData.builtInShipData[random.choice(list(bbData.shipKeysByTL[shipTL]))])
                shipHasPrimary = self.activeShip.maxPrimaries > 0

            for i in range(self.activeShip.maxPrimaries):
                itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                tries = 5
                while len(bbData.weaponObjsByTL[itemTL]) == 0:
                    itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                    tries -= 1
                    if tries == 0:
                        break
                if tries == 0:
                        break
                self.activeShip.equipWeapon(random.choice(bbData.weaponObjsByTL[itemTL]))

            for i in range(random.randint(1, self.activeShip.maxModules)):
                itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                tries = 5
                while len(bbData.moduleObjsByTL[itemTL]) == 0:
                    itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                    tries -= 1
                    if tries == 0:
                        break
                if tries == 0:
                        break
                newModule = random.choice(bbData.moduleObjsByTL[itemTL])
                if self.activeShip.canEquipModuleType(type(newModule)):
                    self.activeShip.equipModule(newModule)

            for i in range(self.activeShip.maxTurrets):
                equipTurret = random.randint(1,100)
                if equipTurret <= bbConfig.criminalEquipTurretChance:
                    itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                    tries = 5
                    while len(bbData.turretObjsByTL[itemTL]) == 0:
                        itemTL = bbConfig.pickRandomItemTL(self.techLevel) - 1
                        tries -= 1
                        if tries == 0:
                            break
                    if tries == 0:
                            break
                    self.activeShip.equipModule(random.choice(bbData.moduleObjsByTL[itemTL]))

            # Purely random loadout generation
            # self.activeShip = bbShip.fromDict(random.choice(list(bbData.builtInShipData.values())))
            # for i in range(self.activeShip.maxPrimaries):
            #     self.activeShip.equipWeapon(random.choice(list(bbData.builtInWeaponObjs.values())))
            # for i in range(random.randint(1, self.activeShip.maxModules)):
            #     moduleNotFound = True
            #     while moduleNotFound:
            #         try:
            #             self.activeShip.equipModule(random.choice(list(bbData.builtInModuleObjs.values())))
            #             moduleNotFound = False
            #         except ValueError:
            #             pass
            # for i in range(self.activeShip.maxTurrets):
            #     equipTurret = random.randint(1,100)
            #     if equipTurret <= 30:
            #         turretNotFound = True
            #         while turretNotFound:
            #             try:
            #                 self.activeShip.equipTurret(random.choice(list(bbData.builtInTurretObjs.values())))
            #                 turretNotFound = False
            #             except ValueError:
            #                 pass
        
        if self.reward == -1:
            self.reward = int(len(self.route) * bbConfig.bPointsToCreditsRatio + self.activeShip.getValue() * bbConfig.shipValueRewardPercentage)
        elif self.reward < 0:
            raise ValueError("Bounty constructor: Invalid reward requested '" + str(self.reward) + "'")
        if self.issueTime == -1.0:
            self.issueTime = datetime.utcnow().replace(second=0).timestamp()
        if self.endTime == -1.0:
            self.endTime = (datetime.utcfromtimestamp(self.issueTime) + timedelta(days=len(self.route))).timestamp()

        if not forceKeepChecked:
            self.checked = {}
        for station in self.route:
            if (not forceKeepChecked) or station not in self.checked or self.checked == {}:
                self.checked[station] = -1

        self.generated = True
        
