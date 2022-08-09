#!/usr/bin/python3
import rospy
from rosnode import get_node_names
from rospy import service
import rospkg
rospack = rospkg.RosPack()


import sys
import xml.etree.ElementTree as ET
from proteus.srv import SymbolTrigger, SymbolDirectional, SymbolTarget, SymbolQuantity
from proteus.soneme import Soneme, SNode, SNodeStatic, SNodeParam
from proteus.siren import SirenConfig

rospy.init_node('ogg_siren_server', argv=None, anonymous=True)

# Farms out the execution of the soneme to the appropriate function
def service_cb(req, soneme):
    rospy.logdebug('Service callback for soneme %s'%(soneme.id))
    if soneme.call_type == 'trigger':
        return execute_trigger(req, soneme)
    elif soneme.call_type == 'directional':
        return execute_directional(req, soneme)
    elif soneme.call_type == 'target':
        return execute_target(req, soneme)
    elif soneme.call_type == 'quantity':
        return execute_quantity(req, soneme)
    else:
        return False

def execute_trigger(req, soneme):
    pass

def execute_directional(req, soneme):
    pass

def execute_target(req, soneme):
    pass

def execute_quantity(req, soneme):
    pass

if __name__ == '__main__':
    rospy.loginfo('Initializing the SIREN server')

    #Check if PROTEUS language server is up
    rospy.loginfo('Checking SIREN language server...')
    lang_server_active = False
    nodes = get_node_names()
    rospy.logdebug(nodes)
    for n in nodes:
        if n.split('/')[-1] == 'proteus_language_server':
            lang_server_active = True
            break
    if not lang_server_active:
        rospy.logerr("This SIREN implementation requires the PROTEUS language server to be active.")
        sys.exit(1)
    else:
        rospy.loginfo('PROTEUS language server OK!')


     # Find soneme language definition file
    rospy.loginfo("Loading vector information...")
    siren_info = rospy.get_param('vectors/out/ClipSIREN')
    siren_def_file = siren_info['definition_file']

    # Find symbol definitions
    rospy.loginfo("Loading symbol information...")
    symbols = rospy.get_param('symbols/out')
    
    # Process soneme definition file into soneme objects
    rospy.loginfo("Loading soneme definitions from symbol definition file.")
    sonemes = dict()

    #Load XML file
    tree = ET.parse(siren_def_file)
    root = tree.getroot()    

    for item in root:
        if item.tag == 'sonemes':
            for sdef in item:
                s = Soneme()
                s.parse_from_xml(sdef)
                sonemes[s.id] = s
        elif item.tag == 'siren-config':
            #Special case for parsing the meta information.
            siren_config = SirenConfig()
            siren_config.parse_from_xml(item)

    # Check for symbol matchup.
    for sym in symbols:
        for key in sonemes:
            s = sonemes[key]
            if sym == s.id:
                rospy.loginfo("Found match beteween symbol %s and soneme %s, associating data."%(sym, s.id))
                rospy.logdebug("Call type: %s"%(symbols.get(sym).get('call_type')))
                s.set_call_type(symbols.get(sym).get('call_type'))
                break
    
    # Setup service calls
    for key, soneme in sonemes.items():
        service_class = None
        if soneme.call_type == 'trigger':
            service_class = SymbolTrigger
        elif soneme.call_type == 'directional':
            service_class = SymbolDirectional
        elif soneme.call_type == 'target':
            service_class = SymbolTarget
        elif soneme.call_type == 'quantity':
            service_class = SymbolQuantity
        else:
            rospy.logwarn("Unexpected call type {} for soneme {}".format(soneme.call_type, soneme.id))

        service_name = 'siren/synth/'+ soneme.name.replace(' ', '_')

        rospy.loginfo('Advertising a service for soneme %s at service endpoint: %s'%(soneme.id, service_name))
        rospy.Service(service_name, service_class, lambda req, soneme=soneme: service_cb(req, soneme))

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        rate.sleep()

else:
    pass