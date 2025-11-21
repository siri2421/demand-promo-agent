# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents import InvocationContext
from google.adk.events.event import Event
from google.adk.utils.context_utils import Aclosing

from ..weather_agent.weather_agent import weather_agent
from ..local_events_agent.local_events_agent import local_events_agent
from ..inventory_agent.inventory_agent import inventory_agent
from ..marketing_agent.marketing_agent import marketing_agent

logger = logging.getLogger(__name__)

class ConditionalSequentialAgent(BaseAgent):
    """
    An agent that runs its sub-agents in sequence, but stops if a stop signal
    is found in the state.
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Runs sub-agents sequentially, checking for a stop signal before each one.
        """
        # Model Armor state check is ignored for the first agent
        agent_id = 0 
        for sub_agent in self.sub_agents:
            print(f"Agent ID: {agent_id}")
            # Since Agent 0 will run checks for itself, allow it to run and only stop execution after it.
            if (ctx.session.state.get("request_stop_signal_found") or ctx.session.state.get("response_stop_signal_found")):
                print(f"Stop signal found. Halting execution of {self.name} Agent ID: {agent_id}.")
                print(f"Request stop signal value: {ctx.session.state['request_stop_signal_found']}")
                print(f"Response stop signal value: {ctx.session.state['response_stop_signal_found']}")
                agent_id += 1 # UNNECESSARY?
                break
            print(f"Running sub-agent {sub_agent.name}")
            async with Aclosing(sub_agent.run_async(ctx)) as agen:
                async for event in agen:
                    yield event
            agent_id += 1

promo_sequence_agent = ConditionalSequentialAgent(
    name="PromoAgent",
    description="Executes a sequence of getting the local weather, getting local events, analyzing inventory for appropriate products, and generating a marketing slogan.",
    sub_agents=[weather_agent, local_events_agent, inventory_agent, marketing_agent]
)
