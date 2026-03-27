from .appliance import ActionBatchAppliance
from .camera import ActionBatchCamera
from .cellularGateway import ActionBatchCellularGateway
from .devices import ActionBatchDevices
from .insight import ActionBatchInsight
from .networks import ActionBatchNetworks
from .organizations import ActionBatchOrganizations
from .sensor import ActionBatchSensor
from .sm import ActionBatchSm
from .switch import ActionBatchSwitch
from .wireless import ActionBatchWireless


# Batch class
class Batch:
    def __init__(self):
        # Action Batch helper API endpoints by section
        self.organizations = ActionBatchOrganizations()
        self.networks = ActionBatchNetworks()
        self.devices = ActionBatchDevices()
        self.appliance = ActionBatchAppliance()
        self.camera = ActionBatchCamera()
        self.cellularGateway = ActionBatchCellularGateway()
        self.insight = ActionBatchInsight()
        self.sensor = ActionBatchSensor()
        self.sm = ActionBatchSm()
        self.switch = ActionBatchSwitch()
        self.wireless = ActionBatchWireless()
