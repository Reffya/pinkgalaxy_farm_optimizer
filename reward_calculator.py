import os
import yaml
from yaml.loader import SafeLoader
from dataclasses import dataclass, field

@dataclass
class Alien:
    name: str
    hp: int
    credits: int
    uridium: int
    isLower: bool

@dataclass
class Launcher:
    name: str
    mag_size: int
    reload_time: int

@dataclass
class Ammo:
    name: str
    multiplier: int
    damage: int
    cost_u: float
    cost_c: int

@dataclass
class Drone_Formation:
    name: str
    rocket_boost: float
    laser_boost: float

@dataclass
class Refining:
    name: str
    boost: float
    cost_u: float

@dataclass
class Loadout:
    lasers: list
    rocket_launcher: Launcher
    rocket_ammos: Ammo
    laser_ammos: Ammo
    launcher_ammos: Ammo
    drone_formation: Drone_Formation
    laser_refining: Refining
    rocket_refining: Refining
    has_leonov: bool
    has_np_boost: bool

@dataclass
class Rewards:
    alien: str
    ttk: float
    raw_uri: float
    uri_w_cost: float
    uri_per_hour: float
    

weapons_file = "weapons.yaml"
aliens_file = "aliens.yaml"
loadout_file = "config.yaml"


def load_datas():
    lasers = {}
    rocket_launchers = {}
    laser_ammos = {}
    launcher_ammos = {}
    rocket_ammos = {}
    drone_formations = {}
    refinings = {}
    aliens = []
    with open(weapons_file) as file:
        data = yaml.load(file, Loader=SafeLoader)
        for laser in data["lasers"]:
            lasers[laser["type"]] = laser["damage"]
        
        for launcher in data["rocket_launchers"]:
            rocket_launchers[launcher["type"]] = Launcher(name=launcher["type"],mag_size=launcher["mag_size"],reload_time=launcher["reload_time"])
        
        for laser_ammo in data["ammos"]["laser"]:
            laser_ammos[laser_ammo["type"]] = Ammo(name=laser_ammo["type"],multiplier=laser_ammo["multiplier"],cost_u=laser_ammo["cost_u"],cost_c=laser_ammo["cost_c"], damage=0)
        
        for launcher_ammo in data["ammos"]["launcher"]:
            launcher_ammos[launcher_ammo["type"]] =  Ammo(name=launcher_ammo["type"],damage=launcher_ammo["damage"],cost_u=launcher_ammo["cost_u"],cost_c=launcher_ammo["cost_c"],multiplier=0)
        
        for rocket_ammo in data["ammos"]["rocket"]:
           rocket_ammos[rocket_ammo["type"]] = Ammo(name=rocket_ammo["type"],damage=rocket_ammo["damage"],cost_u=rocket_ammo["cost_u"],cost_c=rocket_ammo["cost_c"],multiplier=0)
        
        for drone_formation in data["drone_formations"]:
            drone_formations[drone_formation["type"]] = Drone_Formation(name=drone_formation["type"],rocket_boost=drone_formation["rocket_boost"],laser_boost=drone_formation["laser_boost"])

        for refining in data["refining"]:
            refinings[refining["type"]] = Refining(name=refining["type"],boost=refining["boost"],cost_u=refining["cost_u"])

    with open(aliens_file) as file:
        data = yaml.load(file, Loader=SafeLoader)
        for alien in data["aliens"]:
           aliens.append(Alien(name=alien["type"],hp=alien["hp"],credits=alien["rewards"]["credits"],uridium=alien["rewards"]["uridium"],isLower=alien["isLower"])) 

    with open(loadout_file) as file:
        data = yaml.load(file, Loader=SafeLoader)
        laser_config = []
        for laser in data["weapons"]["lasers"]:
            laser_config.append((lasers[laser["type"]],laser["amount"]))
        loadout = Loadout(lasers=laser_config,
            rocket_launcher=rocket_launchers[data["weapons"]["rocket_launcher"]["type"]],
            rocket_ammos=rocket_ammos[data["ammos"]["rockets"]],
            laser_ammos=laser_ammos[data["ammos"]["lasers"]],
            launcher_ammos=launcher_ammos[data["ammos"]["rocket_launcher"]],
            drone_formation=drone_formations[data["drone_formation"]],
            laser_refining=refinings[data["laser_refining"]],
            rocket_refining=refinings[data["rocket_refining"]],
            has_leonov=data["leonov_boost"], has_np_boost=data["beginner_boost"])
        efficiency = data["efficiency"]

    return [aliens, loadout, efficiency]

def computeDPS(loadout: Loadout, isLower: bool):
    avg_dmg = 0.75
    accuracy = 0.8
    beginner_boost_coeff = 0.6 if loadout.has_np_boost else 0
    leonov_rocket_boost = 1 if loadout.has_leonov and isLower else 0
    leonov_laser_boost = 0.5 if loadout.has_leonov and isLower else 0
    laser_refining_coeff = loadout.laser_refining.boost
    rocket_refining_coeff = loadout.rocket_refining.boost
    ammo_multiplier = loadout.laser_ammos.multiplier

    laser_dps = 0
    for laser in loadout.lasers:
        laser_dps = laser_dps + laser[0]*laser[1]
    laser_dps = (laser_dps * ammo_multiplier) * (1 + laser_refining_coeff + leonov_laser_boost + loadout.drone_formation.laser_boost + beginner_boost_coeff) * accuracy

    rocket_dps = loadout.rocket_ammos.damage * ( 1 + rocket_refining_coeff + leonov_rocket_boost + loadout.drone_formation.rocket_boost + beginner_boost_coeff)

    launcher_dps = loadout.launcher_ammos.damage * loadout.rocket_launcher.mag_size / (loadout.rocket_launcher.mag_size + loadout.rocket_launcher.reload_time + beginner_boost_coeff)
    print([laser_dps,rocket_dps,launcher_dps])

    return (laser_dps + rocket_dps + launcher_dps) * avg_dmg 

def computeUriCostPerSec(loadout: Loadout):
    nb_lasers = 0
    for laser in loadout.lasers:
        nb_lasers = nb_lasers + laser[1]
    laser_cost = nb_lasers * (loadout.laser_ammos.cost_u + loadout.laser_refining.cost_u)
    rocket_cost = loadout.rocket_ammos.cost_u + loadout.rocket_refining.cost_u
    launcher_cost = loadout.launcher_ammos.cost_u * loadout.rocket_launcher.mag_size / (loadout.rocket_launcher.mag_size + loadout.rocket_launcher.reload_time)
    return laser_cost + rocket_cost + launcher_cost

def take_uri_hour(elem: Rewards):
    return elem.uri_per_hour

def write_results(bounties: list[Rewards]):
    separator = ","
    output = open("output.csv","w")
    output.write("Alien" + separator + "ttk" + separator + "raw uri" + separator + "uri/kill" + separator + "uri/hour")
    output.write("\n")

    for bounty in bounties:
        output.write(bounty.alien + separator + str(bounty.ttk) + separator + str(bounty.raw_uri) + separator + str(bounty.uri_w_cost) + separator + str(bounty.uri_per_hour))
        output.write("\n")
    output.close()


def main():
    [aliens, loadout, efficiency] = load_datas()
    dps_lower = computeDPS(loadout, True)
    dps_upper = computeDPS(loadout, False)
    uri_cost = computeUriCostPerSec(loadout)
    
    bounties = []
    for alien in aliens:
        ttk = alien.hp/dps_lower if alien.isLower else alien.hp/dps_upper
        if ttk < 1: ttk = 1
        raw_uri =  alien.uridium * 1.6 if loadout.has_np_boost else 1
        bounties.append(Rewards(alien=alien.name,
            raw_uri=alien.uridium,
            ttk=ttk,
            uri_w_cost=alien.uridium - uri_cost * ttk,
            uri_per_hour= (alien.uridium - uri_cost * ttk) * (3600 / ttk) * efficiency))
    bounties.sort(key=take_uri_hour,reverse=True)
    write_results(bounties)


   



if __name__ == "__main__":
    main()
