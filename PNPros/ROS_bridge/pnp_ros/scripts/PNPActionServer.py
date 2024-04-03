#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os

import roslib
import rospy
import actionlib

try:
    sys.path.append(os.environ["PNP_HOME"] + "/scripts")
    sys.path.append(os.environ["PNP_HOME"] + "/actions")
    sys.path.append(os.environ["PNP_HOME"] + "/conditions")
except:
    print("Please set PNP_HOME environment variable to PetriNetPlans folder.")
    sys.exit(1)

from ActionManager import ActionManager
from ConditionManager import ConditionManager
from pnp_msgs.msg import PNPActionFeedback, PNPResult, PNPAction
from pnp_msgs.srv import (
    PNPCondition,
    PNPConditionResponse,
    PNPConditionValue,
    PNPConditionValueResponse,
)

import yaml


import pnp_common
from pnp_common import *

roslib.load_manifest("pnp_ros")
PKG = "pnp_ros"
NODE = "PNPActionServer"
conditionManager = None
actionManager = None


class PNPActionServer(object):
    #  create messages that are used to publish feedback/result
    _feedback = PNPActionFeedback()
    _result = PNPResult()

    def __init__(self, name):
        self._action_server_name = name
        self._as = actionlib.ActionServer(
            self._action_server_name, PNPAction, self.execute_cb, auto_start=False
        )
        self._as.start()
        rospy.loginfo("%s: Action Server started" % self._action_server_name)

    def execute_cb(self, goalhandler):
        r = rospy.Rate(4)
        # init running
        self._feedback.feedback = "running..."
        goalhandler.publish_feedback(self._feedback)
        goal = goalhandler.get_goal()

        # publish info to the console for the user
        rospy.loginfo(
            "%s: Action %s %s" % (self._action_server_name, goal.name, goal.params)
        )
        if goal.function == "start":
            # start executing the action
            actionManager.start_action(goalhandler)
        elif goal.function == "interrupt":
            # print '### Interrupt ',goal.name
            actionManager.interrupt_action(goalhandler)
        elif goal.function == "end":
            # print '### End ',goal.name
            actionManager.end_action(goalhandler)


def handle_PNPConditionEval(req):
    cond_elems = req.cond.split("_")
    cond = cond_elems[0]
    params = cond_elems[1:]

    # evaluate through the condition manager
    cond_truth_value = conditionManager.evaluate(cond, params)

    if cond_truth_value:
        rospy.loginfo(
            "Eval condition: "
            + cond
            + " "
            + " ".join(params)
            + " value: "
            + str(cond_truth_value)
        )

    return PNPConditionResponse(cond_truth_value)


def handle_PNPConditionValue(req):
    cond = req.cond

    cond_value = str(conditionManager.get_value(cond))

    if cond_value:
        # rospy.loginfo('Condition: ' + cond + ' value: ' + cond_value)
        return PNPConditionValueResponse(cond_value)
    else:
        return PNPConditionValueResponse("None")


def get_debug_actions(debug_config_path):
    if not os.path.exists(debug_config_path):
        return {"Debug": False, "msg": "Debug file was not found.", "value": {}}

    with open(debug_config_path) as f:
        debug_actions = yaml.safe_load(f)

    if debug_actions["Debug"]["Active"] is False:
        return {"Debug": False, "msg": "Debug mode is not active", "value": {}}

    mode = debug_actions["Debug"]["Mode"]
    config = debug_actions["Configurations"]

    if mode not in config.keys():
        return {
            "Debug": False,
            "msg": "Debug mode is not found in configurations",
            "value": {},
        }

    if "Active" in config[mode].keys() and config[mode]["Active"] is not None:
        return {
            "Debug": True,
            "msg": "Debug mode active",
            "value": {
                "mode": mode,
                "type": "enable",
                "actions": config[mode]["Active"],
            },
        }

    if "Inactive" in config[mode].keys() and config[mode]["Inactive"] is not None:
        return {
            "Debug": True,
            "msg": "Debug mode active",
            "value": {
                "mode": mode,
                "type": "disable",
                "actions": config[mode]["Inactive"],
            },
        }

    # if no actions are found
    return {"Debug": False, "msg": "Debug mode did not find any actions.", "value": {}}


if __name__ == "__main__":
    rospy.init_node(NODE)
    rospy.set_param('robot_name', 'dummy')

    actions_folder = rospy.get_param("~actions_folder")
    conditions_folder = rospy.get_param("~conditions_folder")

    conditionManager = ConditionManager(conditions_folder)
    actionManager = ActionManager(actions_folder)
    debugConfig =

    # Service which returns truth value of condition
    rospy.Service(SRV_PNPCONDITIONEVAL,
                  PNPCondition,
                  handle_PNPConditionEval)

    # Service which returns value of condition
    rospy.Service(SRV_PNPCONDITIONVALUE,
                  PNPConditionValue,
                  handle_PNPConditionValue)

    PNPActionServer("PNP")

    rospy.spin()
