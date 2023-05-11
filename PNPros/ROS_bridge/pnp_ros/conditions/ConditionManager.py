import os
import rospy
import rosbag
import inspect
import fnmatch

from AbstractCondition import AbstractCondition, ConditionListener
from importlib import util
import std_msgs

class ConditionManager(ConditionListener):


    def __init__(self, conditions_folder=None):
        self.blacklisted_conditions = ["LaserScan", "Twist", "Pose"]
        self._condition_instances = {}

        # Initialize all the classes in current folder + the conditions_folder which implement AbstractCondition
        directory = os.path.dirname(os.path.abspath(__file__))
        potential_files = [os.path.join(dirpath, f)
                    for dirpath, _, files in os.walk(directory, followlinks=True)
                    for f in fnmatch.filter(files, '*.py')]
        if conditions_folder is not None:
            potential_files += [os.path.join(dirpath, f)
                        for dirpath, _, files in os.walk(conditions_folder, followlinks=True)
                        for f in fnmatch.filter(files, '*.py')]
        rospy.logwarn("conditions" + str(potential_files))
        for file in potential_files:
        # for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.py")):

            module_name = os.path.splitext(os.path.basename(file))[0]
            # skip if blacklisted
            if module_name in self.blacklisted_conditions:
                continue

            try:
                spec = util.spec_from_file_location(module_name,file)
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                condition_class = getattr(module, module_name)
                # condition_class = getattr(import_module(full_name, package=""), module_name)
            except (ImportError, AttributeError) as e:
                continue
            else:
                try:
                    if issubclass(condition_class, AbstractCondition) and not inspect.isabstract(condition_class):
                        # Instanciate the condition
                        condition_instance = condition_class()

                        self._condition_instances.update({
                            module_name : condition_instance
                        })

                        rospy.loginfo("Initialized condition " + module_name)
                    else:
                        rospy.logwarn("Class " + module_name + " does not inherit from AbstractCondition or is Abstract")
                except TypeError as e:
                    rospy.logwarn(e)
                    rospy.logwarn("Class " + module_name + " must inherit from AbstractCondition")
                    pass

        # publish conditions updates
        self.cond_update_pub = rospy.Publisher("/condition_update", std_msgs.msg.String, queue_size=10)

        # register itself as a listener of all the conditions
        self.register_condition_listener(self)

    def evaluate(self, condition_name, params):
        try:
            res = self._condition_instances[condition_name].evaluate(params)
            #rospy.loginfo("Evaluating condition " + condition_name + " " + str(params) + ": " + str(res))
            return res
        except KeyError:
            rospy.logwarn("Condition " + condition_name + " not implemented")
            # return true when the condition is not implemented, to avoid loops..
            return True

    def get_value(self, condition_name):
        try:
            res = self._condition_instances[condition_name].get_value()
            #rospy.loginfo("Geting value of condition " + condition_name + ": " + res)
            return res
        except KeyError:
            rospy.logwarn("Condition " + condition_name + " not implemented")
            # return true when the condition is not implemented, to avoid loops..
            return None

    def register_condition_listener(self, listener):
        for (cond_name, cond_instance) in self._condition_instances.items():
            # Register this class as updater listener
            if issubclass(cond_instance.__class__, AbstractCondition):
                cond_instance.register_updates_listener(listener)
                rospy.loginfo(listener.__class__.__name__ + " registered as listener of "\
                            + cond_name)

    # Return a list with the current state of all the conditions
    def get_conditions_dump(self):
        condition_dump = []
        for (cond_name, cond_instance) in self._condition_instances.items():
            condition_dump.append(cond_name + "_" + str(cond_instance.get_value()))

        return condition_dump


    def receive_update(self, condition_instance):
        try:
            self.cond_update_pub.publish(condition_instance.get_name() + "_" + str(condition_instance.get_value()))
        except Exception as e:
            rospy.logerr("Error reading condition state update %s" % e)

    #def get_condition_value(self, cond_name):
    #    cond_value = None
    #    if cond_name in self._condition_instances.keys():
    #        cond_value = str(cond_instance.get_value())

    #    return cond_value
