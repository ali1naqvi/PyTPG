from tpg.program import Program
import pickle
from random import random
import time

"""
Simplified wrapper around a (root) team for easier interface for user.
"""
class ConfAgent:

    """
    Create an agent with a team.
    """
    def init_def(self, team, num=1, actVars=None):
        self.team = team
        self.agentNum = num
        self.actVars = actVars

    """
    Gets an action from the root team of this agent / this agent.
    """
    def act_def(self, state, path_trace):
        start_execution_time = time.time()
        self.actVars["frameNum"] = random()
        visited = list() #Create a new list to track visited team/learners each time
        
        result = None
        path = None
        if path_trace != None:
            path = list()
            result = self.team.act(state, visited=visited, actVars=self.actVars, path_trace=path)
        else:
            result = self.team.act(state, visited=visited, actVars=self.actVars)

        end_execution_time = time.time()
        execution_time = end_execution_time - start_execution_time
        if path_trace != None:
            print("path_trace")
            path_trace['execution_time'] = execution_time
            path_trace['execution_time_units'] = 'seconds'
            path_trace['root_team_id'] = str(self.team.id)
            path_trace['final_action'] = result
            path_trace['path'] = path 
            path_trace['depth'] = len(path)
            print(path_trace)
        return result
    """
    Give this agent/root team a reward for the given task
    """
    def reward_def(self, score, task='task'):
        self.team.outcomes[task] = score

    """
    Check if agent completed this task already, to skip.
    """
    def taskDone_def(self, task):
        return task in self.team.outcomes

    """
    Save the agent to the file, saving any relevant class values to the instance.
    """
    def saveToFile_def(self, fileName):
        pickle.dump(self, open(fileName, 'wb'))
