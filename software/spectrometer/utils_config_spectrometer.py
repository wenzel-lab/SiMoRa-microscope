from lxml import etree as ET

def generate_default_configuration(filename,channel=None):

    top = ET.Element('modes')

    if channel == None or channel == 'Widefield':
        mode_1 = ET.SubElement(top,'mode')
        mode_1.set('ID','1')
        mode_1.set('Name','View Sample')
        mode_1.set('ExposureTime','3')
        mode_1.set('AnalogGain','0')
        mode_1.set('IlluminationSource','11')
        mode_1.set('IlluminationIntensity','10')
        mode_1.set('CameraSN','')
        mode_1.set('Channel','Widefield')
        mode_1.set('DAC_Laser','0')
        mode_1.set('DAC_LED','100')

    if channel == None or channel == 'Widefield':
        mode_2 = ET.SubElement(top,'mode')
        mode_2.set('ID','2')
        mode_2.set('Name','View Laser Spot')
        mode_2.set('ExposureTime','0.01')
        mode_2.set('AnalogGain','0')
        mode_2.set('IlluminationSource','0')
        mode_2.set('IlluminationIntensity','10')
        mode_2.set('CameraSN','')
        mode_2.set('Channel','Widefield')
        mode_2.set('DAC_Laser','80')
        mode_2.set('DAC_LED','0')

    if channel == None or channel == 'Widefield':
        mode_3 = ET.SubElement(top,'mode')
        mode_3.set('ID','3')
        mode_3.set('Name','View Sample + Laser Spot')
        mode_3.set('ExposureTime','3')
        mode_3.set('AnalogGain','0')
        mode_3.set('IlluminationSource','11')
        mode_3.set('IlluminationIntensity','10')
        mode_3.set('CameraSN','')
        mode_3.set('Channel','Widefield')
        mode_3.set('DAC_Laser','60')
        mode_3.set('DAC_LED','80')

    if channel == None or channel == 'Spectrum':
        mode_4 = ET.SubElement(top,'mode')
        mode_4.set('ID','4')
        mode_4.set('Name','Spectrum')
        mode_4.set('ExposureTime','2000')
        mode_4.set('AnalogGain','50')
        mode_4.set('IlluminationSource','0')
        mode_4.set('IlluminationIntensity','10')
        mode_4.set('CameraSN','')
        mode_4.set('Channel','Spectrum')
        mode_4.set('DAC_Laser','100')
        mode_4.set('DAC_LED','0')

    if channel == None or channel == 'Spectrum':
        mode_5 = ET.SubElement(top,'mode')
        mode_5.set('ID','5')
        mode_5.set('Name','Spectrum (Preview)')
        mode_5.set('ExposureTime','100')
        mode_5.set('AnalogGain','100')
        mode_5.set('IlluminationSource','0')
        mode_5.set('IlluminationIntensity','10')
        mode_5.set('CameraSN','')
        mode_5.set('Channel','Spectrum')
        mode_5.set('DAC_Laser','100')
        mode_5.set('DAC_LED','0')

    tree = ET.ElementTree(top)
    tree.write(filename,encoding="utf-8", xml_declaration=True, pretty_print=True)

    print('initialized configuration file ' + filename)