from . import bbToolItem
from .... import bbUtil
from ....bbConfig import bbConfig
from ...bbShipSkin import bbShipSkin
from ...bbShip import bbShip
from ...bbUser import bbUser
from discord import Message
from .... import bbGlobals
import asyncio


class bbShipSkinTool(bbToolItem.bbToolItem):
    """A tool that can be used to apply a skin to a ship.
    This item is named after the skin it applies, and it has no aliases.
    The manufacturer is set to the skin designer.
    This tool is single use. If a calling user is given, the tool is removed from that user's inventory after use.
    """
    def __init__(self, shipSkin : bbShipSkin, value=0, wiki="", icon=bbConfig.defaultShipSkinToolIcon, emoji=bbConfig.defaultShipSkinToolEmoji, techLevel=-1, builtIn=False):
        """
        :param bbShipSkin shipSkin: The skin that this tool applies.
        :param int value: The number of credits that this item can be bought/sold for at a shop. (Default 0)
        :param str wiki: A web page that is displayed as the wiki page for this item. If no wiki is given and shipSkin has one, that will be used instead. (Default "")
        :param str icon: A URL pointing to an image to use for this item's icon (Default bbConfig.defaultShipSkinToolIcon)
        :param bbUtil.dumbEmoji emoji: The emoji to use for this item's small icon (Default bbConfig.defaultShipSkinToolEmoji)
        :param int techLevel: A rating from 1 to 10 of this item's technical advancement. Used as a measure for its effectiveness compared to other items of the same type (Default shipSkin.averageTL)
        :param bool builtIn: Whether this is a BountyBot standard item (loaded in from bbData) or a custom spawned item (Default False)
        """
        super().__init__(name if name else shipSkin.name, aliases, value=value, wiki=wiki if wiki else shipSkin.wiki if shipSkin.hasWiki else "", manufacturer=manufacturer if manufacturer else shipSkin.designer, icon=icon, emoji=emoji, techLevel=techLevel if techLevel > -1 else shipSkin.averageTL, builtIn=builtIn)
        self.shipSkin = shipSkin

    
    async def use(self, *args, **kwargs):
        """Apply the skin to the given ship.
        After use, the tool will be removed from callingBBUser's inventory. To disable this, pass callingBBUser as None.
        """
        if "ship" not in kwargs:
            raise NameError("Required kwarg not given: ship")
        if not isinstance(kwargs["ship"], bbShip):
            raise TypeError("Required kwarg is of the wrong type. Expected bbShip, received " + kwargs["ship"].__class__.__name__)
        if "callingBBUser" not in kwargs:
            raise NameError("Required kwarg not given: callingBBUser")
        if (not isinstance(kwargs["callingBBUser"], bbUser)) and kwargs["callingBBUser"] is not None:
            raise TypeError("Required kwarg is of the wrong type. Expected bbUser or None, received " + kwargs["callingBBUser"].__class__.__name__)
        
        ship, callingBBUser = kwargs["ship"], kwargs["callingBBUser"]

        if not callingBBUser.ownsShip(ship):
            raise RuntimeError("User '" + str(callingBBUser.id) + "' attempted to skin a ship that does not belong to them: " + ship.getNameAndNick())
        
        if ship.isSkinned:
            return ValueError("Attempted to apply a skin to an already-skinned ship")
        if ship.name not in skin.compatibleShips:
            return TypeError("The given skin is not compatible with this ship")
        
        ship.applySkin(self.shipSkin)
        if self in callingBBUser.inactiveTools:
            callingBBUser.inactiveTools.removeItem(self)


    async def userFriendlyUse(self, message : Message, *args, **kwargs) -> str:
        """Apply the skin to the given ship.
        After use, the tool will be removed from callingBBUser's inventory. To disable this, pass callingBBUser as None.

        :param Message message: The discord message that triggered this tool use
        :return: A user-friendly messge summarising the result of the tool use.
        :rtype: str
        """
        if "ship" not in kwargs:
            raise NameError("Required kwarg not given: ship")
        if not isinstance(kwargs["ship"], bbShip):
            raise TypeError("Required kwarg is of the wrong type. Expected bbShip, received " + kwargs["ship"].__class__.__name__)
        if "callingBBUser" not in kwargs:
            raise NameError("Required kwarg not given: callingBBUser")
        if (not isinstance(kwargs["callingBBUser"], bbUser)) and kwargs["callingBBUser"] is not None:
            raise TypeError("Required kwarg is of the wrong type. Expected bbUser or None, received " + kwargs["callingBBUser"].__class__.__name__)
        
        ship, callingBBUser = kwargs["ship"], kwargs["callingBBUser"]

        if not callingBBUser.ownsShip(ship):
            raise RuntimeError("User '" + str(callingBBUser.id) + "' attempted to skin a ship that does not belong to them: " + ship.getNameAndNick())
        
        if ship.isSkinned:
            return ":x: This ship already has a skin applied! Please equip a different ship."
        if ship.name not in skin.compatibleShips:
            return ":x: Your ship is not compatible with this skin! Please equip a different ship, or use `" + bbConfig.commandPrefix + "info skin " + self.name + "` to see what ships are compatible with this skin."
        
        confirmMsg = await message.channel.send("Are you sure you want to apply the " + self.shipSkin.name + " skin to your " + skin.getNameAndNick() + "? Please react to this message to confirm:\n" + defaultAcceptEmoji.sendable + " : Yes\n" + defaultRejectEmoji.sendable + " : Cancel\n\n*This menu will expire in " + str(bbConfig.skinApplyConfirmTimeoutSeconds) + "seconds.*") 
        
        def useConfirmCheck(reactPL):
            return reactPL.message_id == confirmMsg.id and reactPL.user_id == message.author.id and bbUtil.dumbEmojiFromPartial(reactPL.emoji) in [bbConfig.defaultAcceptEmoji, bbConfig.defaultRejectEmoji]

        try:
            reactPL = await bbGlobals.client.wait_for("raw_reaction_add", check=useConfirmCheck, timeout=bbConfig.skinApplyConfirmTimeoutSeconds)
        except asyncio.TimeoutError:
            await confirmMsg.edit(content="This menu has now expired. Please use `" + bbConfig.commandPrefix + "use` again.")
        else:
            if bbUtil.dumbEmojiFromPartial(reactPL.emoji) == bbConfig.defaultAcceptEmoji:
                ship.applySkin(self.shipSkin)
                if self in callingBBUser.inactiveTools:
                    callingBBUser.inactiveTools.removeItem(self)
                
                return "🎨 Success! Your skin has been applied."
            else:
                return "🛑 Skin application cancelled."


    def statsStringShort(self) -> str:
        """Summarise all the statistics and functionality of this item as a string.

        :return: A string summarising the statistics and functionality of this item
        :rtype: str
        """
        return "*Designer: " + self.manufacturer + "*"


    def getType(self) -> type:
        """⚠ DEPRACATED
        Get the type of this object.

        :return: The bbItem class
        :rtype: type
        """
        return bbShipSkinTool

    
    def toDict(self):
        data = super().toDict()
        if self.builtIn:
            return data
        else:
            raise RuntimeError("Attempted to save a non-builtIn bbShipSkinTool")
            
