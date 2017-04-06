"""World of Warships commands for this bot"""
import json
from os.path import join
from threading import Timer
import requests
from discord.ext import commands
from helpers import format_eq, read_json, write_json, get_server_id, is_admin, \
    fopen_generic, generate_image_online
from wows_helpers import find_player_id, warships_today_url, build_embed, \
    calculate_coeff, get_ship_tier_dict


class WorldOfWarships:
    """ WoWs commands """

    def __init__(self, bot, wows_api):
        self.bot = bot
        self.wows_api = wows_api
        self.shame_list = read_json(
            fopen_generic(join('data', 'shamelist.json')))
        na_ships_url = 'https://api.worldofwarships.com/wows/' \
                       'encyclopedia/ships/?application_id={}'.format(
            self.wows_api)
        na_ship_api_response = requests.get(na_ships_url).text
        na_ships_json_data = json.loads(na_ship_api_response)
        write_json(fopen_generic(join('data', 'na_ships.json'), 'w'),
                   na_ships_json_data)
        self.na_ships = read_json(fopen_generic(join('data', 'na_ships.json')))[
            'data']
        self.ssheet = read_json(fopen_generic(join('data', 'sheet.json')))
        self.days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
                     'Friday', 'Saturday']
        self.save_sheet_event = Timer(300, self.save_sheet)
        self.save_shamelist_event = Timer(300, self.save_shamelist)
        self.region_dict = {
            'NA': ['com', 'na'],
            'EU': ['eu'],
            'AS': ['asia'],
            'RU': ['ru']
        }
        self.coefficients = None
        self.expected = None
        self.ship_dict = None
        self.ship_list = None
        self.update_warships_coeff()
        self.update_ship_list()

    def save_sheet(self):
        """ shortcut for saving sheet """
        write_json(fopen_generic(join('data', 'sheet.json'), 'w'), self.ssheet)
        # self.ssheet = read_json(fopen_generic(join('data', 'sheet.json')))
        self.save_sheet_event = Timer(300, self.save_sheet)

    def save_shamelist(self):
        """ shortcut for saving shamelist """
        write_json(fopen_generic(join('data', 'shamelist.json'), 'w'),
                   self.shame_list)
        # self.shame_list = read_json(fopen_generic(join('data', 'shamelist.json')))
        self.save_sheet_event = Timer(300, self.save_shamelist)

    def wows_region(self, region):
        """Return the wows region of a player"""
        return self.region_dict[region][0]

    def warships_region(self, region):
        """Return the warships today region of a player"""
        return self.region_dict[region][-1]

    def update_warships_coeff(self):
        res = calculate_coeff()
        self.coefficients = res[0]
        self.expected = res[1]

    def update_ship_list(self):
        self.ship_dict = get_ship_tier_dict('com', self.wows_api)
        ship_list = []
        for key in self.ship_dict:
            ship_list.append(str(key))
        self.ship_list = ship_list

    @commands.command()
    async def update_wows(self):
        self.update_warships_coeff()
        self.update_ship_list()
        await self.bot.say('Update Success!')

    @commands.command()
    async def ship(self, *input_: str):
        """ look for a ship on the wargaming wiki"""
        ship_dict = None
        ship_name = ' '.join(input_).title()
        if ship_name.startswith('Arp'):
            ship_name = ship_name.replace('Arp', 'ARP')
        for key, val in self.na_ships.items():
            if val['name'] == ship_name:
                ship_dict = val
                break
        if ship_dict is None:
            await self.bot.say("Ship not found!")
            return
        # Format the dictionary so it's human readable
        result = ['```']
        armour = ship_dict['default_profile']['armour']
        # --------------------------------------------------------------------------------------------------------------
        result.append(ship_dict['name'])
        # --------------------------------------------------------------------------------------------------------------
        result.append('Tier: {}'.format(ship_dict['tier']))
        # --------------------------------------------------------------------------------------------------------------
        price_val = '0'
        if ship_dict['price_gold'] != 0:
            price_val = str(ship_dict['price_gold']) + ' Doubloons'
        elif ship_dict['price_credit'] != 0:
            price_val = str(ship_dict['price_credit']) + ' Credits'
        result.append('Price: {}'.format(price_val))
        # --------------------------------------------------------------------------------------------------------------
        result.append('Hit Points: {}'.format(
            ship_dict['default_profile']['hull']['health']))
        # --------------------------------------------------------------------------------------------------------------
        result.append('Citadel armor: {} mm'.format(
            format_eq(armour['citadel']['min'], armour['citadel']['max'])))
        # --------------------------------------------------------------------------------------------------------------
        result.append('Gun Casemate Armor: {} mm'.format
                      (format_eq(armour['casemate']['min'],
                                 armour['casemate']['max'])))
        # --------------------------------------------------------------------------------------------------------------
        result.append('Armoured Deck: {} mm'.format(
            format_eq(armour['deck']['min'], armour['deck']['max'])))
        # --------------------------------------------------------------------------------------------------------------
        result.append('Forward and After Ends Armor: {} mm'.format
                      (format_eq(armour['extremities']['min'],
                                 armour['extremities']['max'])))
        # --------------------------------------------------------------------------------------------------------------
        result.append('```')
        await self.bot.say('\n'.join(result))

    @commands.command(pass_context=True)
    async def shame(self, ctx, user_name: str, region: str = 'NA'):
        """Get shamed by a bot"""
        if region not in ['NA', 'EU', 'RU', 'AS']:
            await self.bot.say('Region must be in ' + str(
                ['NA', 'EU', 'RU', 'AS']) + ' or blank for default(NA)')
            return
        in_list = False
        found = True
        player_id = None
        wows_region = self.wows_region(region)
        warships_region = self.warships_region(region)
        if ctx.message.server is not None and user_name.startswith('<@'):
            server_id = ctx.message.server.id
            if user_name.startswith('<@!'):
                user_name = user_name[3:-1]
            else:
                user_name = user_name[2:-1]
            if server_id in self.shame_list \
                    and user_name in self.shame_list[server_id]:
                player_id = self.shame_list[server_id][user_name][1]
                warships_region = self.shame_list[server_id][user_name][0]
                wows_region = warships_region if \
                    warships_region != 'na' else 'com'
                in_list = True
        if not in_list:
            player_id = find_player_id(wows_region, self.wows_api, user_name)
            found = player_id is not None
        if found:
            result = build_embed(wows_region, self.wows_api, player_id,
                                 self.coefficients,
                                 self.expected, self.ship_dict, self.ship_list)
            if result is not None:
                await self.bot.send_message(ctx.message.channel, embed=result)
            else:
                fn = generate_image_online(
                    warships_today_url(warships_region, player_id),
                    join('data', 'dark.png'))
                await self.bot.send_file(ctx.message.channel, fn)
        else:
            await self.bot.say('Player not found!')

    @commands.command(pass_context=True)
    async def shamelist(self, ctx):
        """Get the entire shame shamelist"""
        server_id = get_server_id(ctx)
        if server_id in self.shame_list:
            res = [ctx.message.server.get_member(key).name for key in
                   self.shame_list[server_id]]
            await self.bot.say('```{}```'.format(', '.join(res))) if res else \
                await self.bot.say('This server\'s shamelist is empty!')
        else:
            await self.bot.say('This server\'s shamelist is empty!')

    @commands.command(pass_context=True)
    async def addshame(self, ctx, user_name: str, region: str = 'NA'):
        """Add you to the shame shamelist"""
        if region not in ['NA', 'EU', 'RU', 'AS']:
            await self.bot.say('Region must be in ' + str(
                ['NA', 'EU', 'RU', 'AS']) + ' or blank for default(NA)')
            return
        new_entry = False
        user_id = str(ctx.message.author.id)
        server_id = str(ctx.message.server.id)
        playerid = find_player_id(self.wows_region(region), self.wows_api,
                                  user_name)
        if ctx.message.server.id not in self.shame_list:
            self.shame_list[server_id] = {}
            new_entry = True
        if user_id not in self.shame_list[server_id]:
            self.shame_list[server_id][user_id] = None
            new_entry = True
        self.shame_list[ctx.message.server.id][user_id] = [
            self.warships_region(region), playerid]
        self.save_shamelist()
        await self.bot.say('Add success!') if new_entry else await self.bot.say(
            'Edit Success!')

    @commands.command(pass_context=True)
    async def removeshame(self, ctx):
        """Remove you from the shame shamelist"""
        server_id = ctx.message.server.id
        if str(ctx.message.author.id) in self.shame_list[server_id]:
            self.shame_list[server_id].pop(str(ctx.message.author.id), None)
            self.save_shamelist()
            await self.bot.say('Remove success!')
        else:
            await self.bot.say(
                'Removed failed, you were not in the shamelist to begin with.')

    @commands.command(pass_context=True)
    async def newsheet(self, ctx):
        if not is_admin(ctx, ctx.message.author.id):
            await self.bot.say('This is an admin only command!')
        else:
            self.ssheet[str(get_server_id(ctx))] = {}
            self.save_sheet()
            await self.bot.say(
                'New spread sheet created! The old one has been removed!')

    @commands.command(pass_context=True)
    async def addmatch(self, ctx, matchname: str, *datetime):
        if not is_admin(ctx, ctx.message.author.id):
            await self.bot.say('This is an admin only command!')
        elif str(get_server_id(ctx)) not in self.ssheet:
            await self.bot.say('Your server doesn\'t seem to have a spreadsheet'
                               ', please consult `?help newsheet`')
        elif not datetime or datetime[0] not in self.days:
            await self.bot.say('Please enter a valid date!')
        else:
            self.ssheet[str(get_server_id(ctx))][matchname] = {}
            datetime = list(datetime)
            datetime[0] += ','
            self.ssheet[str(get_server_id(ctx))][matchname]['time'] = datetime
            self.ssheet[str(get_server_id(ctx))][matchname]['players'] = []
            self.save_sheet()
            await self.bot.say('Match on {} added!'.format(' '.join(datetime)))

    @commands.command(pass_context=True)
    async def removematch(self, ctx, matchname):
        if not is_admin(ctx, ctx.message.author.id):
            await self.bot.say('This is an admin only command!')
        elif str(get_server_id(ctx)) not in self.ssheet:
            await self.bot.say('Your server doesn\'t seem to have a '
                               'spreadsheet, please consult `?help newsheet`')
        elif matchname not in self.ssheet[str(get_server_id(ctx))]:
            await self.bot.say('There doesn\'t seem to be a with that name.')
        else:
            del self.ssheet[str(get_server_id(ctx))][matchname]
            self.save_sheet()
            await self.bot.say('Match: {} removed!'.format(matchname))

    @commands.command(pass_context=True)
    async def joinmatch(self, ctx, *matchname):
        if str(get_server_id(ctx)) not in self.ssheet:
            await self.bot.say(
                'Your server doesn\'t seem to have a spreadsheet, '
                'please consult `?help newsheet`')
            return
        else:
            joined = []
            for name in matchname:
                try:
                    if ctx.message.author.id not in \
                            self.ssheet[str(get_server_id(ctx))][name][
                                'players']:
                        self.ssheet[str(get_server_id(ctx))][name][
                            'players'].append(ctx.message.author.id)
                        joined.append(name)
                except KeyError:
                    continue
            self.save_sheet()
            await self.bot.say(
                'You have joined matches: {}'.format(', '.join(joined)))

    @commands.command(pass_context=True)
    async def quitmatch(self, ctx, *matchname):
        if str(get_server_id(ctx)) not in self.ssheet:
            await self.bot.say(
                'Your server doesn\'t seem to have a spreadsheet,'
                ' please consult `?help newsheet`')
            return
        else:
            quits = []
            for name in matchname:
                if name in self.ssheet[str(get_server_id(ctx))]:
                    try:
                        self.ssheet[str(get_server_id(ctx))][name][
                            'players'].remove(ctx.message.author.id)
                        quits.append(name)
                    except ValueError:
                        continue
            self.save_sheet()
            await self.bot.say(
                'You have quit the matches: {}'.format(' ,'.join(quits)))

    @commands.command(pass_context=True)
    async def sheet(self, ctx):
        if str(get_server_id(ctx)) not in self.ssheet:
            await self.bot.say(
                'Your server doesn\'t seem to have a spreadsheet, '
                'please consult `?help newsheet`')
            return
        else:
            if self.ssheet[str(get_server_id(ctx))] == {}:
                await self.bot.say('There doesn\'t seem to be any '
                                   'matches in this spread sheet!')
                return
            else:
                res = [
                    '{}: {}\nPlayers: {}\nPlayer count: {}'.format(
                        ' '.join(val['time']),
                        key,
                        ', '.join(
                            [ctx.message.server.get_member(player).name for
                             player in val['players']]),
                        len(val['players'])
                    )
                    for key, val in
                    self.ssheet[str(get_server_id(ctx))].items()]
                res.sort(key=lambda x: self.days.index(x[0:x.find(',')]))
                await self.bot.say('```{}```'.format('\n\n'.join(res)))
