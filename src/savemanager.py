import os
import sys

import getpass
import platform
import glfw
import imgui
from PIL import Image
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer

from hldlib import HLDSaveFile
from typing import Any

if os.getenv("XDG_SESSION_TYPE") == "wayland":
    os.environ["XDG_SESSION_TYPE"] = "x11"

if "path.txt" in os.listdir("."):
    with open("path.txt", "r") as f: PATH_TO_SAVES = f.readline().rstrip()
else:
    match platform.system():
        case "Windows":
            PATH_TO_SAVES = f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\HyperLightDrifter"
            SAVELIFE_NAME_FORMAT = "HyperLight_RecordOfTheDrifter_{}.sav"
        case "Darwin":
            PATH_TO_SAVES = f"/Users/{getpass.getuser()}/Library/Application Support/com.HeartMachine.HyperLightDrifter"
            SAVELIFE_NAME_FORMAT = "hyperlight_recordofthedrifter_{}.sav"
        case "Linux":
            PATH_TO_SAVES = f"/home/{getpass.getuser()}/.config/HyperLightDrifter"
            SAVELIFE_NAME_FORMAT = "hyperlight_recordofthedrifter_{}.sav"
        case _: raise ValueError("Please specify savefile path with a 'path.txt'")
    
LOADED_SAVE: HLDSaveFile = None # type: ignore

class GLOBAL:
    """
    This is basically the global state
    """
    save_name_field = ""
    north_modules = {
        "-1895481": "in rm_NC_CrushArena",
        "-813235": "in rm_NL_AltarThrone",
        "-902212": "in rm_NL_DropArena",
        "-932471": "in rm_NL_DropSpiralOpen",
        "-1084059": "in rm_NL_ShrinePath2VAULT",
        "-767783": "in rm_NL_StairAscent",
        "-1137428": "in rm_NX_NorthHall",
        "-1047430": "in rm_NX_TowerLock"
    }
    east_modules = {
            "-53392": "in rm_EA_BogTempleCamp",
            "-255100": "in rm_EA_WaterTunnelLAB",
            "-167326": "in rm_EB_FlamePitLAB",
            "-68841": "in rm_EC_BigBogLAB",
            "-118694": "in rm_EC_DocksLab",
            "-18778": "in rm_EC_EastLoop",
            "-88709": "in rm_EL_FrogArena",
            "-187905": "in rm_EL_MegaHugeLAB",
        }
    west_modules = {
            "435082": "in rm_WB_TanukiTrouble",
            "403666": "in rm_WC_BigMeadowVAULT",
            "266784": "in rm_WC_CliffsideCellsRedux",
            "206139": "in rm_WC_MeadowoodCorner",
            "335443": "in rm_WC_PrisonHallEnd",
            "353953": "in rm_WC_ThinForestLowSecret",
            "101387": "in rm_WL_PrisonHALVAULT",
            "185267": "in rm_WT_TheWood",
        }
    south_modules = {
            "-398635": "in rm_CH_APillarBird",
            "-555279": "in rm_CH_CEndHall",
            "-596678": "in rm_CH_CGateBlock",
            "-386457": "in rm_CH_CSpiral",
            "-602007": "in rm_CH_TABigOne",
            "-417825": "in rm_S_GauntletLinkup",
            "-416223": "in rm_S_GauntletLinkup",
            "-676357": "in rm_S_Gauntlet_Elevator",
        }
    north_tablets = {"1":"in rm_NL_EntrancePath","2":"in rm_NC_NPCHatchery","3":"in rm_NX_SpiralStaircase",
                     "4":"in rm_NL_RisingArena"}
    east_tablets = {"9":"in rm_EB_DeadOtterWalk","10":"in rm_EC_ThePlaza",
                     "11":"in rm_EA_BogTempleCamp","12":"in rm_EC_EastLoop"}
    west_tablets = {"13":"in rm_WA_Grotto_buffIntro","14":"in rm_WB_TreeTreachery",
                     "15":"in rm_WA_TitanFalls", "16": "in rm_WA_MultiEntranceLab"}
    south_tablets = {"5":"in rm_SX_SouthOpening","6":"in rm_CH_ACorner",
                    "7":"in rm_CH_CTurnHall","8":"in rm_CH_CGateBlock"}
    outfits = {
            "0": "NG",
            "1": "Blue",
            "2": "Fuschia" ,
            "3": "White",
            "4": "Yellow",
            "5": "Orange",
            "6": "Blue/Green",
            "7": "Pink",
            "8": "Black",
            "9": "Ochre",
            "10": "Purple",
            "11": "NG+"
        }
    guns = {
            "0": "None",
            "1": "Pistol",
            "2": "Zaliska",
            "21": "Laser Gun",
            "23": "Railgun",
            "41": "Shotgun",
            "43": "Diamond Shotgun"
        }
    skills = {
            "1": "Charge Slash",
            "2": "Projectile Reflect",
            "3": "Phantom Slash",
            "4": "Chaindash",
            "5": "Projectile Shield",
            "6": "Dash Stab"
        }
    wells = {"1": "North Warp","0": "East Warp",  "2": "West Warp", "3": "South Warp", "4": "Central"}
    pylons = {"1": "North Pylon","0": "East Pylon",  "2": "West Pylon", "3": "South Pylon"}
    bosses = {
        "0": "Cleaner",
        "1": "JerkPope",
        "2": "OldGeneral",
        "3.10": "MarkScythe",
        "3.20": "BennyArrow",
        "3.30": "BulletBaker",
        "3.40": "CountAlucard"
    }
    error_state = False
    error_text = ""

        
def handle_list(value_desc: dict[str, str], list_in_question: list[str], title: str = "", salt: str = ""):
    """
    Creates a list of checkboxes from value_desc
    Each time you check or uncheck one of the checkboxes it appends/removes the value from the list

    NOTE: because i'm stupid value_desc dictionary keys are the values and the actual dictionary values are the descriptions
    """
    for value, desc in value_desc.items():
        _, check = imgui.checkbox(f"{desc}##{salt}{value}", value in list_in_question)
        if   check and value not in list_in_question: list_in_question.append(value)
        elif not check and value in list_in_question: list_in_question.remove(value)

def handle_dict(value_desc: dict[str, str], dict_in_question: dict[str, list[str]], title: str = "", salt: str = "", default_list: list[str] = []):
    """
    Creates a list of checkboxes and text inputs from value_desc
    Checkboxes control what keys are present in the dictionary
    Text inputs control the dictionary values (i basically dump all data handling on the user)

    NOTE: because i'm stupid value_desc dictionary keys are the values and the actual dictionary values are the descriptions
    """
    imgui.columns(2)
    dict_keys = dict_in_question.keys()
    for value, desc in value_desc.items():
        _, check = imgui.checkbox(f"{desc}##{salt}{value}", value in dict_keys)
        imgui.next_column()
        _, text = imgui.input_text(f"{title}##{salt}{value}", " ".join(dict_in_question.get(value, default_list)), 16)
        if   check : dict_in_question[value] = text.split()
        elif not check and value in dict_keys: dict_in_question.pop(value)
        imgui.next_column()
    imgui.columns(1)

def handle_list_combo(value_desc: dict[str, str], list_in_question: list[str], value_in_question: Any, title: str = "", salt: str = "") -> Any:
    """
    Creates a combo box that lets you choose a value from a list

    NOTE: because i'm stupid value_desc dictionary keys are the values and the actual dictionary values are the descriptions
    """
    value_copy = value_in_question # THIS IS NOT A REAL COPY BECAUSE WE ARE WORKING WITH STR AND FLOATS HERE
    if isinstance(value_copy, float): value_copy = int(value_copy)
    value_copy = str(value_copy)
    owned = {key: value for key, value in value_desc.items() if key in list_in_question}
    vals = list(owned.keys())
    descs = list(owned.values())
    if value_copy in vals:
        index = vals.index(value_copy)
    else: index = 0
    _, index = imgui.combo(f"{title}##{salt}", index, descs)
    return value_in_question.__class__(vals[index]) if len(vals) else value_in_question

def handle_int(val: float, title: str, salt: str = "") -> float:
    """
    Creates an int input

    Returns the value back so use it like: THE_THING_I_WHAT_TO_SET = handle_int(THE_THING_I_WHAT_TO_SET, "the thing")
    """
    _, val = imgui.input_int(f"{title}##{salt}", int(val))
    return float(val)

def handle_float(val: float, title: str, salt: str = "") -> float:
    """
    Creates a float input

    Returns the value back so use it like: THE_THING_I_WHAT_TO_SET = handle_float(THE_THING_I_WHAT_TO_SET, "the thing")
    """
    _, val = imgui.input_float(f"{title}##{salt}", val)
    return val

def handle_bool(val: float, title: str, salt: str = "") -> float:
    """
    Creates a checkbox

    Returns the value back so use it like: THE_THING_I_WHAT_TO_SET = handle_bool(THE_THING_I_WHAT_TO_SET, "the thing")
    """
    _, check = imgui.checkbox(f"{title}##{salt}", bool(val))
    return float(check)

def handle_str(val: str, title: str, salt: str = "") -> str:
    """
    Creates a text input

    Returns the value back so use it like: THE_THING_I_WHAT_TO_SET = handle_str(THE_THING_I_WHAT_TO_SET, "the thing")
    """
    _, val = imgui.input_text(f"{title}##{salt}", val, 15)
    return val


def load(save_name: str):
    global LOADED_SAVE
    try:
        LOADED_SAVE = HLDSaveFile.load(os.path.join(PATH_TO_SAVES, SAVELIFE_NAME_FORMAT.format(save_name)))
        LOADED_SAVE.cCapes.append("0")
        LOADED_SAVE.cSwords.append("0")
        LOADED_SAVE.cShells.append("0")
        LOADED_SAVE.sc.append("0")
    except FileNotFoundError as e:
        error("Couldn't load savefile")

def save(save_name: str):
    try:
        if LOADED_SAVE is not None:
            if LOADED_SAVE.checkRoom not in LOADED_SAVE.rooms: LOADED_SAVE.rooms.append(str(LOADED_SAVE.checkRoom))
            LOADED_SAVE.dump(os.path.join(PATH_TO_SAVES, SAVELIFE_NAME_FORMAT.format(save_name)))
    except:
        error("Couldn't save savefile")

def delete(save_name: str):
    try:
        os.remove(os.path.join(PATH_TO_SAVES, SAVELIFE_NAME_FORMAT.format(save_name)))
    except:
        error("Couldn't remove savefile")

def debug_dump():
    try:
        if LOADED_SAVE is not None:
            LOADED_SAVE.debug_dump("debug_dump.json")
    except:
        error("Couldn't debug dump savefile")

def error(title: str):
    GLOBAL.error_state = True
    GLOBAL.error_text = title


def frame_commands():
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    io = imgui.get_io()

    if io.key_ctrl and io.keys_down[glfw.KEY_Q]:
        sys.exit(0)

    # Saves window
    if True:
        imgui.set_next_window_position(0,0)
        imgui.set_next_window_size(850-200-250,220)
        imgui.begin("Saves")

        all_savefiles = [file_name.split('_', 2)[2].replace(".sav", "") for file_name in os.listdir(PATH_TO_SAVES) if "hyperlight_recordofthedrifter_" in file_name.lower()]
        imgui.columns(2)
        imgui.begin_child("Savess")
        for save_name in all_savefiles:
            if imgui.button(save_name, width=200-40):
                GLOBAL.save_name_field = save_name
        imgui.end_child()
        imgui.next_column()
        imgui.push_item_width(imgui.get_window_content_region_width())
        _, GLOBAL.save_name_field = imgui.input_text("##savefield", GLOBAL.save_name_field, 16, flags=imgui.INPUT_TEXT_CHARS_NO_BLANK)
        if imgui.button("Load"): load(GLOBAL.save_name_field); GLOBAL.save_name_field = ""
        imgui.same_line()
        if imgui.button("Save"): save(GLOBAL.save_name_field); GLOBAL.save_name_field = ""
        imgui.same_line()
        if imgui.button("Delete"):delete(GLOBAL.save_name_field); GLOBAL.save_name_field = ""
        imgui.new_line()
        if imgui.button("Debug Dump"): debug_dump()

        imgui.end()

    # OVERWORLD WINDOW
    if LOADED_SAVE is not None:
        imgui.set_next_window_position(0,800-580)
        imgui.set_next_window_size(850,580)
        imgui.begin("Overworld and Meta")

        # MODULES
        imgui.text("Modules")
        imgui.separator()

        imgui.begin_group()

        imgui.begin_group()
        imgui.text("North")
        handle_list(GLOBAL.north_modules, LOADED_SAVE.cl.setdefault("6", []))
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("East")
        handle_list(GLOBAL.east_modules, LOADED_SAVE.cl.setdefault("7", []))
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("West")
        handle_list(GLOBAL.west_modules, LOADED_SAVE.cl.setdefault("9", []))
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("South")
        handle_list(GLOBAL.south_modules, LOADED_SAVE.cl.setdefault("8", []))
        imgui.end_group()

        imgui.end_group()
        imgui.new_line()

        # TABLETS
        imgui.text("Monoliths")
        imgui.separator()

        imgui.begin_group()

        imgui.begin_group()
        imgui.text("North")
        handle_list(GLOBAL.north_tablets,LOADED_SAVE.tablet)
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("East")
        handle_list(GLOBAL.east_tablets,LOADED_SAVE.tablet)
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("West")
        handle_list(GLOBAL.west_tablets,LOADED_SAVE.tablet)
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("South")
        handle_list(GLOBAL.south_tablets,LOADED_SAVE.tablet)
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.end_group()
        imgui.new_line()

        imgui.columns(2)

        # WARPS AND PYLONS
        imgui.text("Warps, Pylons, and Meta")
        imgui.separator()

        imgui.begin_group()
        imgui.text("Warp Points")
        handle_list(GLOBAL.wells, LOADED_SAVE.warp)
        imgui.end_group()

        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("Pylons")
        handle_list(GLOBAL.pylons, LOADED_SAVE.well)
        imgui.end_group()

        imgui.next_column()

        imgui.begin_group()
        imgui.text("Meta")
        LOADED_SAVE.gameName = handle_str(LOADED_SAVE.gameName, "Savefile Name")
        LOADED_SAVE.fireplaceSave = handle_bool(LOADED_SAVE.fireplaceSave, "Savefile Beaten")
        LOADED_SAVE.charDeaths = handle_int(LOADED_SAVE.charDeaths, "Deaths")
        LOADED_SAVE.playT = handle_int(LOADED_SAVE.playT, "Playtime (min)")

        imgui.end_group()


        imgui.end()
    
    # EQUIPMENT WINDOW
    if LOADED_SAVE is not None:
        imgui.set_next_window_position(850,0)
        imgui.set_next_window_size(380,800)
        imgui.begin("Equipment")
        imgui.push_item_width(imgui.get_window_width() * .2)
        imgui.text("GEAR")
        imgui.separator()
        imgui.begin_group()
        imgui.text("Capes")
        handle_list(GLOBAL.outfits, LOADED_SAVE.cCapes, salt="capes")
        LOADED_SAVE.cape = handle_list_combo(GLOBAL.outfits, LOADED_SAVE.cCapes, LOADED_SAVE.cape, "", salt="capes")
        imgui.end_group()
        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("Swords")
        handle_list(GLOBAL.outfits, LOADED_SAVE.cSwords, salt="swords")
        LOADED_SAVE.sword = handle_list_combo(GLOBAL.outfits, LOADED_SAVE.cSwords, LOADED_SAVE.sword, "", salt="swords")
        imgui.end_group()

        imgui.same_line(spacing=12)
        
        imgui.begin_group()
        imgui.text("Companions")
        handle_list(GLOBAL.outfits, LOADED_SAVE.cShells, salt="comps")
        LOADED_SAVE.compShell = handle_list_combo(GLOBAL.outfits, LOADED_SAVE.cShells, LOADED_SAVE.compShell, "", salt="comps")
        imgui.end_group()

        imgui.new_line()

        imgui.text("WEAPONS")
        imgui.separator()
        imgui.begin_group()
        imgui.text("Weapons")
        handle_list(GLOBAL.guns, LOADED_SAVE.sc, salt="lg")
        imgui.end_group()

        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("Upgraded Weapons")
        handle_list(GLOBAL.guns, LOADED_SAVE.scUp, salt="upgrades")
        imgui.end_group()

        imgui.same_line(spacing=12)

        imgui.begin_group()
        imgui.text("Equipped")
        LOADED_SAVE.eq00 = handle_list_combo(GLOBAL.guns, LOADED_SAVE.sc, LOADED_SAVE.eq00, "", salt="eq00")
        LOADED_SAVE.eq01 = handle_list_combo(GLOBAL.guns, LOADED_SAVE.sc, LOADED_SAVE.eq01, "", salt="eq01")
        imgui.end_group()

        imgui.new_line()

        imgui.text("OTHER THINGS")
        imgui.separator()

        imgui.begin_group()
        imgui.text("Skills")
        handle_list(GLOBAL.skills, LOADED_SAVE.skill, "skills")
        imgui.end_group()

        imgui.same_line(spacing=12)
    
        imgui.begin_group()
        imgui.text("Other")
        LOADED_SAVE.drifterkey = handle_int(LOADED_SAVE.drifterkey, "Keys")
        LOADED_SAVE.gear = handle_int(LOADED_SAVE.gear, "Gearbits")
        LOADED_SAVE.specialUp = handle_int(LOADED_SAVE.specialUp, "Grenades")
        LOADED_SAVE.healthUp = handle_int(LOADED_SAVE.healthUp, "Bonus Healthkits")
        LOADED_SAVE.hasMap = handle_bool(LOADED_SAVE.hasMap, "Has Map")
        imgui.end_group()

        imgui.end()
    
    # DRIFTER WINDOW
    if LOADED_SAVE is not None:
        imgui.set_next_window_position(850-200,0)
        imgui.set_next_window_size(200,220)
        imgui.begin("Drifter")
        imgui.push_item_width(imgui.get_window_width() * .5)

        LOADED_SAVE.checkHP = handle_int(LOADED_SAVE.checkHP, "HP")
        LOADED_SAVE.checkStash = handle_int(LOADED_SAVE.checkStash, "Health Kits")
        LOADED_SAVE.checkBat = handle_float(LOADED_SAVE.checkBat, "Ammo%")
        LOADED_SAVE.checkAmmo = handle_float(LOADED_SAVE.checkAmmo*100, "Grenades%")/100
        LOADED_SAVE.CH = handle_bool(LOADED_SAVE.CH, "Alt Drifter")
        # if not LOADED_SAVE.CH:
        #     LOADED_SAVE.noviceMode = handle_bool(LOADED_SAVE.noviceMode, "Novice Mode")
        LOADED_SAVE.checkX = handle_int(LOADED_SAVE.checkX, "X")
        LOADED_SAVE.checkY = handle_int(LOADED_SAVE.checkY, "Y")
        LOADED_SAVE.checkRoom = handle_int(LOADED_SAVE.checkRoom, "Room")
        imgui.end()

    # BOSSES WINDOW
    if LOADED_SAVE is not None:
        imgui.set_next_window_position(850-200-250,0)
        imgui.set_next_window_size(250,220)
        imgui.begin("Bosses")
        handle_dict(GLOBAL.bosses, LOADED_SAVE.bosses, "", "bosses", ["0", "0"])
        imgui.end()

    # ERROR MANAGEMENT
    if GLOBAL.error_state:
        imgui.open_popup("Error")
    if imgui.begin_popup_modal("Error")[0]:
        imgui.text(GLOBAL.error_text)
        imgui.separator()
        if imgui.button("OK##error"):
            imgui.close_current_popup()
            GLOBAL.error_state = False
        imgui.end_popup()

def render_frame(impl, window, font):
    glfw.poll_events()
    impl.process_inputs()
    imgui.new_frame()

    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    if font is not None:
        imgui.push_font(font)
    frame_commands()
    if font is not None:
        imgui.pop_font()

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)

def impl_glfw_init():
    width, height = 1230, 800
    window_name = "HLSaveManager"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    
    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)
    # with Image.open(os.path.abspath(os.path.join(os.path.dirname(__file__), "res", "icon.ico"))) as icon:
    #     glfw.set_window_icon(window, 1, icon)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window

def main():
    imgui.create_context()
    window = impl_glfw_init()

    impl = GlfwRenderer(window)

    io = imgui.get_io()
    io.ini_saving_rate = 0
    impl.refresh_font_texture()

    while not glfw.window_should_close(window):
        render_frame(impl, window, None)

    impl.shutdown()
    glfw.terminate()

if __name__ == "__main__":
    main()
