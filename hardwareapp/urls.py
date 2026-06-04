from django.urls import path
from hardwareapp import views
app_name = 'hardwareapp'


urlpatterns = [
    # Machine (first in hardware)
    path('machine/', views.MachineListView.as_view(), name='machine_list'),
    path('machine/data/', views.MachineListDataView.as_view(), name='machine_list_data'),
    path('machine/create/', views.MachineCreateView.as_view(), name='machine_create'),
    path('machine/<int:pk>/', views.MachineDetailView.as_view(), name='machine_detail'),
    path('machine/<int:pk>/history/', views.MachineHistoryView.as_view(), name='machine_history'),
    path('machine/<int:pk>/edit/', views.MachineUpdateView.as_view(), name='machine_update'),
    path('machine/<int:pk>/copy/', views.MachineCopyView.as_view(), name='machine_copy'),
    path('machine/<int:pk>/delete/', views.MachineDeleteView.as_view(), name='machine_delete'),
    path('machine/api/component-options/', views.MachineComponentOptionsAPIView.as_view(), name='machine_api_component_options'),

    # Operating System
    path('os/', views.OSListView.as_view(), name='os_list'),
    path('os/data/', views.OSListDataView.as_view(), name='os_list_data'),
    path('os/create/', views.OSCreateView.as_view(), name='os_create'),
    path('os/<int:pk>/', views.OSDetailView.as_view(), name='os_detail'),
    path('os/<int:pk>/edit/', views.OSUpdateView.as_view(), name='os_update'),
    path('os/<int:pk>/copy/', views.OSCopyView.as_view(), name='os_copy'),
    path('os/<int:pk>/delete/', views.OSDeleteView.as_view(), name='os_delete'),

    # Processor
    path('processor/', views.ProcessorListView.as_view(), name='processor_list'),
    path('processor/data/', views.ProcessorListDataView.as_view(), name='processor_list_data'),
    path('processor/create/', views.ProcessorCreateView.as_view(), name='processor_create'),
    path('processor/<int:pk>/', views.ProcessorDetailView.as_view(), name='processor_detail'),
    path('processor/<int:pk>/edit/', views.ProcessorUpdateView.as_view(), name='processor_update'),
    path('processor/<int:pk>/copy/', views.ProcessorCopyView.as_view(), name='processor_copy'),
    path('processor/<int:pk>/delete/', views.ProcessorDeleteView.as_view(), name='processor_delete'),

    # Graphics Card
    path('graphics-card/', views.GraphicsCardListView.as_view(), name='graphics_card_list'),
    path('graphics-card/data/', views.GraphicsCardListDataView.as_view(), name='graphics_card_list_data'),
    path('graphics-card/create/', views.GraphicsCardCreateView.as_view(), name='graphics_card_create'),
    path('graphics-card/<int:pk>/', views.GraphicsCardDetailView.as_view(), name='graphics_card_detail'),
    path('graphics-card/<int:pk>/edit/', views.GraphicsCardUpdateView.as_view(), name='graphics_card_update'),
    path('graphics-card/<int:pk>/copy/', views.GraphicsCardCopyView.as_view(), name='graphics_card_copy'),
    path('graphics-card/<int:pk>/delete/', views.GraphicsCardDeleteView.as_view(), name='graphics_card_delete'),

    # Motherboard
    path('motherboard/', views.MotherboardListView.as_view(), name='motherboard_list'),
    path('motherboard/data/', views.MotherboardListDataView.as_view(), name='motherboard_list_data'),
    path('motherboard/create/', views.MotherboardCreateView.as_view(), name='motherboard_create'),
    path('motherboard/<int:pk>/', views.MotherboardDetailView.as_view(), name='motherboard_detail'),
    path('motherboard/<int:pk>/edit/', views.MotherboardUpdateView.as_view(), name='motherboard_update'),
    path('motherboard/<int:pk>/copy/', views.MotherboardCopyView.as_view(), name='motherboard_copy'),
    path('motherboard/<int:pk>/delete/', views.MotherboardDeleteView.as_view(), name='motherboard_delete'),

    # RAM
    path('ram/', views.RAMListView.as_view(), name='ram_list'),
    path('ram/data/', views.RAMListDataView.as_view(), name='ram_list_data'),
    path('ram/create/', views.RAMCreateView.as_view(), name='ram_create'),
    path('ram/<int:pk>/', views.RAMDetailView.as_view(), name='ram_detail'),
    path('ram/<int:pk>/edit/', views.RAMUpdateView.as_view(), name='ram_update'),
    path('ram/<int:pk>/copy/', views.RAMCopyView.as_view(), name='ram_copy'),
    path('ram/<int:pk>/delete/', views.RAMDeleteView.as_view(), name='ram_delete'),

    # HDD
    path('hdd/', views.HDListView.as_view(), name='hdd_list'),
    path('hdd/data/', views.HDListDataView.as_view(), name='hdd_list_data'),
    path('hdd/create/', views.HDCreateView.as_view(), name='hdd_create'),
    path('hdd/<int:pk>/', views.HDDetailView.as_view(), name='hdd_detail'),
    path('hdd/<int:pk>/edit/', views.HDUpdateView.as_view(), name='hdd_update'),
    path('hdd/<int:pk>/copy/', views.HDCopyView.as_view(), name='hdd_copy'),
    path('hdd/<int:pk>/delete/', views.HDDeleteView.as_view(), name='hdd_delete'),

    # SSD
    path('ssd/', views.SSDListView.as_view(), name='ssd_list'),
    path('ssd/data/', views.SSDListDataView.as_view(), name='ssd_list_data'),
    path('ssd/create/', views.SSDCreateView.as_view(), name='ssd_create'),
    path('ssd/<int:pk>/', views.SSDDetailView.as_view(), name='ssd_detail'),
    path('ssd/<int:pk>/edit/', views.SSDUpdateView.as_view(), name='ssd_update'),
    path('ssd/<int:pk>/copy/', views.SSDCopyView.as_view(), name='ssd_copy'),
    path('ssd/<int:pk>/delete/', views.SSDDeleteView.as_view(), name='ssd_delete'),

    # Liquid Cooler
    path('liquid-cooler/', views.LiquidCoolerListView.as_view(), name='liquid_cooler_list'),
    path('liquid-cooler/data/', views.LiquidCoolerListDataView.as_view(), name='liquid_cooler_list_data'),
    path('liquid-cooler/create/', views.LiquidCoolerCreateView.as_view(), name='liquid_cooler_create'),
    path('liquid-cooler/<int:pk>/', views.LiquidCoolerDetailView.as_view(), name='liquid_cooler_detail'),
    path('liquid-cooler/<int:pk>/edit/', views.LiquidCoolerUpdateView.as_view(), name='liquid_cooler_update'),
    path('liquid-cooler/<int:pk>/copy/', views.LiquidCoolerCopyView.as_view(), name='liquid_cooler_copy'),
    path('liquid-cooler/<int:pk>/delete/', views.LiquidCoolerDeleteView.as_view(), name='liquid_cooler_delete'),

    # UPS
    path('ups/', views.UPSListView.as_view(), name='ups_list'),
    path('ups/data/', views.UPSListDataView.as_view(), name='ups_list_data'),
    path('ups/create/', views.UPSCreateView.as_view(), name='ups_create'),
    path('ups/<int:pk>/', views.UPSDetailView.as_view(), name='ups_detail'),
    path('ups/<int:pk>/edit/', views.UPSUpdateView.as_view(), name='ups_update'),
    path('ups/<int:pk>/copy/', views.UPSCopyView.as_view(), name='ups_copy'),
    path('ups/<int:pk>/delete/', views.UPSDeleteView.as_view(), name='ups_delete'),

    # Monitor
    path('monitor/', views.MonitorListView.as_view(), name='monitor_list'),
    path('monitor/data/', views.MonitorListDataView.as_view(), name='monitor_list_data'),
    path('monitor/create/', views.MonitorCreateView.as_view(), name='monitor_create'),
    path('monitor/<int:pk>/', views.MonitorDetailView.as_view(), name='monitor_detail'),
    path('monitor/<int:pk>/edit/', views.MonitorUpdateView.as_view(), name='monitor_update'),
    path('monitor/<int:pk>/copy/', views.MonitorCopyView.as_view(), name='monitor_copy'),
    path('monitor/<int:pk>/delete/', views.MonitorDeleteView.as_view(), name='monitor_delete'),

    # Keyboard
    path('keyboard/', views.KeyboardListView.as_view(), name='keyboard_list'),
    path('keyboard/data/', views.KeyboardListDataView.as_view(), name='keyboard_list_data'),
    path('keyboard/create/', views.KeyboardCreateView.as_view(), name='keyboard_create'),
    path('keyboard/<int:pk>/', views.KeyboardDetailView.as_view(), name='keyboard_detail'),
    path('keyboard/<int:pk>/edit/', views.KeyboardUpdateView.as_view(), name='keyboard_update'),
    path('keyboard/<int:pk>/copy/', views.KeyboardCopyView.as_view(), name='keyboard_copy'),
    path('keyboard/<int:pk>/delete/', views.KeyboardDeleteView.as_view(), name='keyboard_delete'),

    # Mouse
    path('mouse/', views.MouseListView.as_view(), name='mouse_list'),
    path('mouse/data/', views.MouseListDataView.as_view(), name='mouse_list_data'),
    path('mouse/create/', views.MouseCreateView.as_view(), name='mouse_create'),
    path('mouse/<int:pk>/', views.MouseDetailView.as_view(), name='mouse_detail'),
    path('mouse/<int:pk>/edit/', views.MouseUpdateView.as_view(), name='mouse_update'),
    path('mouse/<int:pk>/copy/', views.MouseCopyView.as_view(), name='mouse_copy'),
    path('mouse/<int:pk>/delete/', views.MouseDeleteView.as_view(), name='mouse_delete'),

    # Headphone
    path('headphone/', views.HeadphoneListView.as_view(), name='headphone_list'),
    path('headphone/data/', views.HeadphoneListDataView.as_view(), name='headphone_list_data'),
    path('headphone/create/', views.HeadphoneCreateView.as_view(), name='headphone_create'),
    path('headphone/<int:pk>/', views.HeadphoneDetailView.as_view(), name='headphone_detail'),
    path('headphone/<int:pk>/edit/', views.HeadphoneUpdateView.as_view(), name='headphone_update'),
    path('headphone/<int:pk>/copy/', views.HeadphoneCopyView.as_view(), name='headphone_copy'),
    path('headphone/<int:pk>/delete/', views.HeadphoneDeleteView.as_view(), name='headphone_delete'),

    # Pentable
    path('pentable/', views.PentableListView.as_view(), name='pentable_list'),
    path('pentable/data/', views.PentableListDataView.as_view(), name='pentable_list_data'),
    path('pentable/create/', views.PentableCreateView.as_view(), name='pentable_create'),
    path('pentable/<int:pk>/', views.PentableDetailView.as_view(), name='pentable_detail'),
    path('pentable/<int:pk>/edit/', views.PentableUpdateView.as_view(), name='pentable_update'),
    path('pentable/<int:pk>/copy/', views.PentableCopyView.as_view(), name='pentable_copy'),
    path('pentable/<int:pk>/delete/', views.PentableDeleteView.as_view(), name='pentable_delete'),

    # Speaker
    path('speaker/', views.SpeakerListView.as_view(), name='speaker_list'),
    path('speaker/data/', views.SpeakerListDataView.as_view(), name='speaker_list_data'),
    path('speaker/create/', views.SpeakerCreateView.as_view(), name='speaker_create'),
    path('speaker/<int:pk>/', views.SpeakerDetailView.as_view(), name='speaker_detail'),
    path('speaker/<int:pk>/edit/', views.SpeakerUpdateView.as_view(), name='speaker_update'),
    path('speaker/<int:pk>/copy/', views.SpeakerCopyView.as_view(), name='speaker_copy'),
    path('speaker/<int:pk>/delete/', views.SpeakerDeleteView.as_view(), name='speaker_delete'),

    # Webcam
    path('webcam/', views.WebcamListView.as_view(), name='webcam_list'),
    path('webcam/data/', views.WebcamListDataView.as_view(), name='webcam_list_data'),
    path('webcam/create/', views.WebcamCreateView.as_view(), name='webcam_create'),
    path('webcam/<int:pk>/', views.WebcamDetailView.as_view(), name='webcam_detail'),
    path('webcam/<int:pk>/edit/', views.WebcamUpdateView.as_view(), name='webcam_update'),
    path('webcam/<int:pk>/copy/', views.WebcamCopyView.as_view(), name='webcam_copy'),
    path('webcam/<int:pk>/delete/', views.WebcamDeleteView.as_view(), name='webcam_delete'),

    # Power Supply
    path('power-supply/', views.PowerSupplyListView.as_view(), name='power_supply_list'),
    path('power-supply/data/', views.PowerSupplyListDataView.as_view(), name='power_supply_list_data'),
    path('power-supply/create/', views.PowerSupplyCreateView.as_view(), name='power_supply_create'),
    path('power-supply/<int:pk>/', views.PowerSupplyDetailView.as_view(), name='power_supply_detail'),
    path('power-supply/<int:pk>/edit/', views.PowerSupplyUpdateView.as_view(), name='power_supply_update'),
    path('power-supply/<int:pk>/copy/', views.PowerSupplyCopyView.as_view(), name='power_supply_copy'),
    path('power-supply/<int:pk>/delete/', views.PowerSupplyDeleteView.as_view(), name='power_supply_delete'),

    # Cabinet
    path('cabinet/', views.CabinetListView.as_view(), name='cabinet_list'),
    path('cabinet/data/', views.CabinetListDataView.as_view(), name='cabinet_list_data'),
    path('cabinet/create/', views.CabinetCreateView.as_view(), name='cabinet_create'),
    path('cabinet/<int:pk>/', views.CabinetDetailView.as_view(), name='cabinet_detail'),
    path('cabinet/<int:pk>/edit/', views.CabinetUpdateView.as_view(), name='cabinet_update'),
    path('cabinet/<int:pk>/copy/', views.CabinetCopyView.as_view(), name='cabinet_copy'),
    path('cabinet/<int:pk>/delete/', views.CabinetDeleteView.as_view(), name='cabinet_delete'),
]
