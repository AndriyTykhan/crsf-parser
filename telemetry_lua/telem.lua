-- BASIC EdgeTX Telemetry Script for Radiomaster Boxer
-- We'll build this step by step!

-- Screen size for Boxer
local LCD_W = 480
local LCD_H = 272

-- This function runs ONCE when the script first loads
local function init()
    -- We'll add initialization code here later
end

-- This function runs EVERY refresh (about 20-30 times per second)
local function run(event)
    
    -- Step 1: Clear the screen to black
    lcd.clear()
    
    -- Step 2: Draw some basic text
    -- Format: lcd.drawText(x, y, "text", flags)
        local rssi = getValue("RSSI")
    lcd.drawText(10, 140, "RSSI: " .. rssi, 0)
    lcd.drawText(10, 10, "Hello EdgeTX!", 0)
    lcd.drawText(10, 40, "Screen size: ", rssi, 0)
    
    -- Step 3: Draw a simple shape
    -- Format: lcd.drawRectangle(x, y, width, height, flags)
    lcd.drawRectangle(10, 70, 100, 50, 0)
    
    -- Step 4: Draw a filled rectangle
    -- Format: lcd.drawFilledRectangle(x, y, width, height, flags)
    lcd.drawFilledRectangle(200, 70, 60, 60, 0)
    
    -- Step 5: Get a simple telemetry value (RSSI - always available)
    local rssi = getValue("RSSI")
    lcd.drawText(10, 140, "RSSI: " .. rssi, 0)
    
    -- Step 6: Show script is running
    local time = getTime() -- Gets time in 1/100th seconds since radio turned on
    lcd.drawText(10, 170, "Running: " .. time, 0)
    
    -- Return 0 to tell EdgeTX everything is OK
    return 0
end

-- This is required - tells EdgeTX which functions to use
return { init=init, run=run }