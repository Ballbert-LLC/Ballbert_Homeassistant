import json

import requests

from Hal import initialize_assistant
from Hal.Classes import Response
from Hal.Decorators import reg
from Hal.Skill import Skill

assistant = initialize_assistant()


class HomeAssistant(Skill):
    def __init__(self):
        pass

    def query_homeassistant(self, enpoint, method="get", data={}):
        api_key = self.get("API_KEY")
        url = self.get("URL")

        full_url = f"http://{url}/{enpoint}"

        if method == "get":
            result = requests.get(full_url, headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }, data=data)
        elif method == "post":
            result = requests.post(full_url, headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }, data=json.dumps(data))

        try:
            json_data = json.loads(result.text)
        except Exception as e:
            json_data = result.text
            print(json_data)

        return json_data

    @reg(name="get_all_entites")
    def get_entities(self):
        json_data = self.query_homeassistant("api/states")

        entity_ids = []
        for state in json_data:
            entity_id = state["entity_id"]
            entity_ids.append(entity_id)
        entity_ids.sort()
        return Response(True, data=entity_ids)

    @reg(name="turn_on_device")
    def handle_turn_on_intent(self, entity: str) -> None:
        """
        Turns on a homeassistant device

        :param string entity: The device you want to turn on domains must have a turn_off endpoint. Ex. Light
        """

        result = self.query_homeassistant(
            f"api/services/homeassistant/turn_on",
            method="post",
            data={
                "entity_id": entity,
            }
        )
        return Response(True, data=result)

    @reg('turn_off_device')
    def handle_turn_off_intent(self, entity) -> None:
        """
        Turns off a homeassistant device

        :param string entity: The device you want to turn off domains must have a turn_off endpoint. Ex. Light
        """
        result = self.query_homeassistant(
            f"api/services/homeassistant/turn_off",
            method="post",
            data={
                "entity_id": entity,
            }
        )
        return Response(True, data=result)

    @reg('open_device')
    def handle_open(self, entity) -> None:
        """
        Opens a homeassistant device

        :param string entity: The device you want to open must be of domain cover
        """
        domain = entity.split(".")[0]

        if domain == "cover":
            result = self.query_homeassistant(
                f"api/services/{domain}/open_cover",
                method="post",
                data={
                    "entity_id": entity,
                }
            )
            return Response(True, data=result)
        else:
            return Response(False)

    @reg('close_device')
    def handle_close(self, entity) -> None:
        """
        Closes homeassistant device

        :param string entity: The device you want to close must be of domain cover
        """
        domain = entity.split(".")[0]

        if domain == "cover":
            result = self.query_homeassistant(
                f"api/services/{domain}/close_cover",
                method="post",
                data={
                    "entity_id": entity,
                }
            )
            return Response(True, data=result)
        else:
            return Response(False)

    @reg('stop_device')
    def handle_stop(self, entity) -> None:
        """
        Stops a homeassistant device

        :param string entity: The device you want to stop must be of domain cover
        """

        domain = entity.split(".")[0]

        if domain == "cover":
            result = self.query_homeassistant(
                f"api/services/{domain}/stop_cover",
                method="post",
                data={
                    "entity_id": entity,
                }
            )
            return Response(True, data=result)
        else:
            return Response(False)

    @reg('toggle_device')
    def handle_toggle_intent(self, entity) -> None:
        """
        Toggles a homeassistant device

        :param string entity: The device you want to toggle
        """
        result = self.query_homeassistant(
            f"api/services/homeassistant/toggle",
            method="post",
            data={
                "entity_id": entity,
            }
        )
        return Response(True, data=result)

    @reg('read_sensor_or_device_state')
    def handle_sensor_intent(self, sensor_name) -> None:
        """
        Reads the state of a homeassitant sensor or device.

        :param string sensor_name: The sensor you want to read
        """

        json_data = self.query_homeassistant(f"api/states/{sensor_name}")

        state = json_data["state"]
        return Response(True, data=state)

    @reg('set_light_brightness')
    def handle_light_set_intent(self, light, brightness) -> None:
        """
        Sets a homeassistant light's brightness.

        :param string light: The light you want to set brightness.
        :param number brightness: The brightness you want to set the light to
        """
        brightness_req = brightness
        if brightness_req > 100:
            brightness_req = 100
        elif brightness_req < 0:
            brightness_req = 0
        brightness_value = int(brightness_req / 100 * 255)
        brightness_percentage = int(brightness_req)

        ha_data = {'entity_id': light}

        # IDEA: set context for 'turn it off again' or similar
        # self.set_context('Entity', ha_entity['dev_name'])
        # Set values for HA
        ha_data['brightness'] = brightness_value
        result = self.query_homeassistant(
            f"api/services/light/turn_on",
            method="post",
            data=ha_data
        )
        return Response(True, data=f"Brightness set to {brightness_percentage}")

    @reg('increase_light_brightness')
    def handle_light_increase_intent(self, light) -> None:
        """
        Increases a homeassistant light's brightness.

        :param string light: The light you want to increase the brightness.
        """
        brightness_req = 10.0
        brightness_value = int(brightness_req / 100 * 255)

        # Set the min and max brightness for bulbs. Smart bulbs
        # use 0-255 integer brightness, while spoken commands will
        # use 0-100% brightness.
        min_brightness = 5
        max_brightness = 255

        ha_data = {'entity_id': light}

        current_brightness = self.handle_sensor_intent(light)

        ha_data['brightness'] = current_brightness + \
            brightness_value

        if ha_data['brightness'] > max_brightness:
            ha_data['brightness'] = max_brightness

        if ha_data["brightness"] < min_brightness:
            ha_data["brightness"] = min_brightness

        result = self.query_homeassistant(
            f"api/services/light/turn_on",
            method="post",
            data=ha_data
        )

        brightness_persentage = ha_data["brightness"]/255 * 100

        return Response(True, data=f"Brightness set to {brightness_persentage}")

    @reg('decrease_light_brightness')
    def handle_light_decrease_intent(self, light) -> None:
        """
        Decreases a homeassistant light's brightness.

        :param string light: The light you want to decrease the brightness.
        """
        brightness_req = 10.0
        brightness_value = int(brightness_req / 100 * 255)

        # Set the min and max brightness for bulbs. Smart bulbs
        # use 0-255 integer brightness, while spoken commands will
        # use 0-100% brightness.
        min_brightness = 5
        max_brightness = 255

        ha_data = {'entity_id': light}

        current_brightness = self.handle_sensor_intent(light)

        ha_data['brightness'] = current_brightness - \
            brightness_value

        if ha_data['brightness'] > max_brightness:
            ha_data['brightness'] = max_brightness

        if ha_data["brightness"] < min_brightness:
            ha_data["brightness"] = min_brightness

        result = self.query_homeassistant(
            f"api/services/light/turn_on",
            method="post",
            data=ha_data
        )

        brightness_persentage = ha_data["brightness"]/255 * 100

        return Response(True, data=f"Brightness set to {brightness_persentage}")

    @reg('trigger_automation')
    def handle_automation_intent(self, automation) -> None:
        """
        Trigger a homeassistant automation id.

        :param string automation: The automation id you want to call.
        """
        result = self.query_homeassistant(
            f"api/services/automation/trigger",
            method="post",
            data={
                "entity_id": automation
            }
        )

        return Response(True, data=result)

    @reg('set_climate')
    def handle_set_thermostat_intent(self, entity, value) -> None:
        """
        Trigger a homeassistant tracker.

        :param string tracker: The light you want to decrease the brightness.
        :param number value: What you want to set the themostat to
        """

        # API endpoint to set thermostat temperature
        api_endpoint = f"services/climate/set_temperature"

        # Data for the request payload
        data = {
            "entity_id": entity,
            "temperature": value
        }

        response = self.query_homeassistant(
            api_endpoint, method="post", data=data)

        return Response(True, data=response)
