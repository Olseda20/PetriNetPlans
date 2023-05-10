import rospy
from abc import ABC, abstractmethod

class AbstractCondition(ABC):

    def __init__(self):
        self._updates_listeners = []

    @abstractmethod
    def evaluate(self, params):
        raise NotImplementedError()

    @abstractmethod
    def get_value(self):
        raise NotImplementedError()


class ConditionListener(ABC):

    @abstractmethod
    def receive_update(self, condition_name, condition_value):
        raise NotImplementedError()
