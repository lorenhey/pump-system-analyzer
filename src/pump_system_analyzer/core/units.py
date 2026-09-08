import pint

# Create a central unit registry for the entire application
ureg = pint.UnitRegistry()

# Define common units for the application
ureg.define("m3_per_h = m**3 / h = m3/h")
ureg.define("L_per_s = L / s = L/s")
ureg.define("gpm = gallon / minute")
ureg.define("barg = bar; offset: 0") # Note: pint handles absolute/gauge carefully. We will use absolute mainly, or handle gauge explicitly.

Q_ = ureg.Quantity

def get_base_units():
    return {
        "length": ureg.meter,
        "mass": ureg.kilogram,
        "time": ureg.second,
        "temperature": ureg.kelvin,
        "pressure": ureg.pascal,
        "energy": ureg.joule,
        "power": ureg.watt
    }
