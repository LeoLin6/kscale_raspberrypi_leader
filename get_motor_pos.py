from pykos import KOS
import asyncio

async def get_actuator_positions():
    kos = KOS("127.0.0.1")  # Connect to KOS service
    
    # Get all actuator states
    resp = await kos.actuator.get_actuators_state()
    
    for state in resp.states:
        print(f"Actuator {state.actuator_id}: {state.position:.2f}° at {state.velocity:.2f}°/s")

# Run it
asyncio.run(get_actuator_positions())