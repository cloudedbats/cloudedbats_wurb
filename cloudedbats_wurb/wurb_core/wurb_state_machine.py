#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import time
import queue
import threading
import logging

class WurbStateMachine(object):
    """ State machine engine. Makes it easier to handle a system with a limited 
        amount of valid states where state transitions can have many triggers. 
        Also promotes a more modular design of the overall system. 
        Two queues are used to avoid concurrency effects. """
    def __init__(self):
        """ """
        self._logger = logging.getLogger('CloudedBatsWURB')
        #
        self._state_machine_dict = {}
        self._perform_action_function = None
        self._current_state = 'idle'
        #
        self._active = False
        self._event_queue = queue.Queue()
        self._event_thread = None
        self._action_queue = queue.Queue()
        self._action_thread = None
    
    def load_states(self, state_machine_data):
        """ Example: state_machine_data =
                [{'states': ['current_state_1', 'current_state_2', ], 
                  'events': ['event_1', 'event_2', ], 
                  'new_state': 'new_state', 
                  'actions': ['action_1', 'action_2', ] },
                ] """
        self._state_machine_dict = {}
        self._prepare_state_machine_dict(state_machine_data)
    
    def set_perform_action_function(self, perform_action_function):
        """ Define callback function for actions. """
        self._perform_action_function = perform_action_function
    
    def set_current_state(self, current_state):
        """ """
        self._current_state = current_state
    
    def event(self, event):
        """ """
        self._logger.debug('State machine: Event added to queue: ' + event)
        if self._active:
            try:
                self._event_queue.put(event, block=False)
            except:
                self._logger.error('State machine: Event queue is full. Event dropped.')
    
    def start(self):
        """ Activates the two queues."""
        self._active = True
        # Start events in thread.
        self._target_thread = threading.Thread(target=self._event_exec, args=[])
        self._target_thread.start()
        # Start actions in thread.
        self._target_thread = threading.Thread(target=self._action_exec, args=[])
        self._target_thread.start()
    
    def stop(self):
        """ Terminates the state machine. """
        self._active = False
        # Queue triggers if waiting for timeout.
        try:
            self._event_queue.put(False)
            self._action_queue.put(False)
        except:
            pass
    
    def _event_exec(self):
        """ Running in thread for events. """
        while self._active:
            # Get from queue.
            try:
                event = self._event_queue.get(timeout=1.0)
                if event is False:
                    break # Terminated.
            except:
                continue # No event available. (Don't lock thread.)
            #
            self._logger.info('State machine: Event executed: ' + event)                
            key = (self._current_state, event)
            key_wildcard = ('*', event)
            if key in self._state_machine_dict:
                # Check for exact match.
                (new_state, actions) = self._state_machine_dict[key]
                # Keep old state if *.
                if new_state != '*':
                    self._logger.info('State machine: Old state: ' + self._current_state + '   New state: ' + new_state)                
                    self._current_state = new_state
                #
                for action in actions:
                    time.sleep(0.1) # Release thread.
                    try:
                        self._action_queue.put(action, block=False)
                    except:
                        self._logger.error('State machine: Action queue is full. Action dropped.')
            # Check for wildcards.
            elif key_wildcard in self._state_machine_dict:
                #
                (new_state, actions) = self._state_machine_dict[key_wildcard]
                # Keep old state if *.
                if new_state != '*':
                    self._logger.info('State machine: Old state: ' + self._current_state + '   New state: ' + new_state)                
                    self._current_state = new_state
                for action in actions:
                    time.sleep(0.1) # Release thread.
                    try:
                        self._action_queue.put(action, block=False)
                    except:
                        self._logger.error('State machine: Action queue is full. Action dropped.')
            else:
                self._logger.error('State machine: Can not find state/event: ' + self._current_state + '/' + event)
    
    def _action_exec(self):
        """ Running in thread for actions. """
        self._logger.debug('State machine: _action_exec.')
        while self._active:
            # Get from queue.
            try:
                action = self._action_queue.get(timeout=1.0)
                if action is False:
                    break # Terminated.
            except:
                continue # No action available. (Don't lock thread.)
            #
            self._perform_action_function(action)
    
    def _prepare_state_machine_dict(self, state_machine_data):
        """ Converts:
            [{'states': ['init'], 'events': ['setup'], 'new_state': 'idle', 
             'actions': ['do_something', 'do_something_more',] },]
            into:
            {(init, setup): (idle, ['do_something', 'do_something_more',]),}
        """
        for row_dict in state_machine_data:
            states = row_dict.get('states', '')
            events = row_dict.get('events', '')
            new_state = row_dict.get('new_state', '')
            actions = row_dict.get('actions', '')
            #
            for state in states:
                for event in events:
                    key = (state, event)
                    value = (new_state, actions)
                    #
                    if key not in self._state_machine_dict:
                        self._state_machine_dict[key] = value
                    else:
                        self._logger.debug('State machine state/even already exists: ' + 
                              str(key) )

