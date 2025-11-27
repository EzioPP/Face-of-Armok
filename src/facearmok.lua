-- ============================================================================
-- CONSTANTS
-- ============================================================================

local json = require('json')
local luasocket = require('plugins.luasocket')

local API_URL = "http://localhost:3000/api/dwarf" -- Change this to your API endpoint

local THRESHOLDS = {
    VERY_SMALL = 25,
    SMALL = 50,
    SOMEWHAT_SMALL = 75,
    SLIGHTLY_BELOW = 90,
    SLIGHTLY_ABOVE = 110,
    LARGE = 125,
    VERY_LARGE = 150,
    EXTREMELY_LARGE = 175
}

local LENGTH_THRESHOLDS = {
    STUBBLE = 25,
    SHORT = 50,
    MEDIUM = 100,
    LONG = 150,
    VERY_LONG = 200
}

local EQUIPMENT_CATEGORIES = {
    [df.inv_item_role_type.Worn] = "worn",
    [df.inv_item_role_type.WrappedAround] = "worn",
    [df.inv_item_role_type.Strapped] = "worn",
    [df.inv_item_role_type.Weapon] = "wielded",
    [df.inv_item_role_type.Hauled] = "other"
}

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Convert length value to description
local function length_to_desc(length)
    if length < 0 then return "N/A"
    elseif length == 0 then return "clean-shaven"
    elseif length < LENGTH_THRESHOLDS.STUBBLE then return "stubble"
    elseif length < LENGTH_THRESHOLDS.SHORT then return "short"
    elseif length < LENGTH_THRESHOLDS.MEDIUM then return "medium length"
    elseif length < LENGTH_THRESHOLDS.LONG then return "long"
    elseif length < LENGTH_THRESHOLDS.VERY_LONG then return "very long"
    else return "extremely long"
    end
end

-- Get style name from enum
local function get_style_name(style_enum)
    local styles = {
        [0] = "neatly combed",
        [1] = "braided",
        [2] = "double braids",
        [3] = "pony tails",
        [4] = "clean shaven"
    }
    return styles[style_enum] or "styled"
end

-- Generic value-to-description converter
local function value_to_description(value, category)
    local t = THRESHOLDS

    -- Different descriptions based on category
    local descriptions = {
        body_modifier = {
            "very short/small", "short/small", "somewhat short/small",
            "slightly below average", "average", "slightly above average",
            "tall/large", "very tall/large", "extremely tall/large"
        },
        body_part = {
            "very small", "small", "somewhat small",
            "slightly below average", "average", "slightly above average",
            "large", "very large", "extremely large"
        }
    }

    local desc_set = descriptions[category] or descriptions.body_part

    if value < t.VERY_SMALL then return desc_set[1]
    elseif value < t.SMALL then return desc_set[2]
    elseif value < t.SOMEWHAT_SMALL then return desc_set[3]
    elseif value < t.SLIGHTLY_BELOW then return desc_set[4]
    elseif value < t.SLIGHTLY_ABOVE then return desc_set[5]
    elseif value < t.LARGE then return desc_set[6]
    elseif value < t.VERY_LARGE then return desc_set[7]
    elseif value < t.EXTREMELY_LARGE then return desc_set[8]
    else return desc_set[9]
    end
end

-- Get tissue type name by searching through tissue styles
local function get_tissue_name(tissue_type_id, caste_raw)
    if not caste_raw.tissue_styles then
        return "unknown"
    end

    for i = 0, #caste_raw.tissue_styles - 1 do
        local tissue_def = caste_raw.tissue_styles[i]
        if tissue_def and tissue_def.id == tissue_type_id then
            -- Try noun first (like "hair", "beard"), then token (like "HAIR", "BEARD")
            if tissue_def.noun and tissue_def.noun ~= "" then
                return tissue_def.noun
            elseif tissue_def.token and tissue_def.token ~= "" then
                return tissue_def.token:lower()
            end
        end
    end
    return "unknown"
end


-- ============================================================================
-- DATA COLLECTION FUNCTIONS
-- ============================================================================

-- Get body modifiers data
local function get_body_modifiers(appearance, caste_raw)
    local data = {}
    if not appearance.body_modifiers or #appearance.body_modifiers == 0 then
        return data
    end

    for i = 0, #appearance.body_modifiers - 1 do
        local modifier_value = appearance.body_modifiers[i]
        -- Check if we have a corresponding definition
        if i < #caste_raw.body_appearance_modifiers then
            local modifier_def = caste_raw.body_appearance_modifiers[i]
            if modifier_def and modifier_def.modifier then
                local name = modifier_def.modifier.noun or ("modifier_" .. i)
                local desc = value_to_description(modifier_value, "body_modifier")
                table.insert(data, {
                    name = name,
                    value = modifier_value,
                    description = desc
                })
            end
        end
    end
    return data
end

-- Get body part modifiers data
local function get_bp_modifiers(appearance, caste_raw)
    local data = {}
    if not appearance.bp_modifiers or #appearance.bp_modifiers == 0 then
        return data
    end

    -- Only show the ones that have valid definitions
    local max_index = math.min(#appearance.bp_modifiers - 1, #caste_raw.bp_appearance.modifiers - 1)
    for i = 0, max_index do
        local modifier_value = appearance.bp_modifiers[i]
        local modifier_def = caste_raw.bp_appearance.modifiers[i]
        if modifier_def and modifier_def.modifier and modifier_def.modifier.noun and modifier_def.modifier.noun ~= "" then
            local desc = value_to_description(modifier_value, "body_part")
            table.insert(data, {
                name = modifier_def.modifier.noun,
                value = modifier_value,
                description = desc
            })
        end
    end
    return data
end

-- Get color modifiers data
local function get_color_modifiers(appearance, caste_raw)
    local data = {}

    if not appearance.colors or #appearance.colors == 0 then
        return data
    end

    for i = 0, #appearance.colors - 1 do
        local color_value = appearance.colors[i]
        if i < #caste_raw.color_modifiers then
            local color_def = caste_raw.color_modifiers[i]
            if color_def and color_value >= 0 and color_value < #color_def.pattern_index then
                -- Get the pattern index (which points to a descriptor_pattern)
                local pattern_index = color_def.pattern_index[color_value]

                -- Look up the pattern in the world descriptors
                if pattern_index >= 0 and pattern_index < #df.global.world.raws.descriptors.patterns then
                    local pattern = df.global.world.raws.descriptors.patterns[pattern_index]
                    if pattern then
                        -- Get the color name from the pattern's ID (like "AMETHYST", "GRAY", etc.)
                        local color_name = pattern.id
                        if color_name and color_name ~= "" then
                            table.insert(data, {
                                part = color_def.part,
                                color = color_name:lower()
                            })
                        else
                            -- Fallback: try to get the first color from the pattern's color list
                            if pattern.colors and #pattern.colors > 0 then
                                local color_idx = pattern.colors[0]
                                if color_idx >= 0 and color_idx < #df.global.world.raws.descriptors.colors then
                                    local color = df.global.world.raws.descriptors.colors[color_idx]
                                    if color and color.name then
                                        table.insert(data, {
                                            part = color_def.part,
                                            color = color.name
                                        })
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    return data
end

-- Get tissue styles (hair, beard, etc.)
local function get_tissue_styles(appearance, caste_raw)
    local data = {}

    if not appearance.tissue_style_type or #appearance.tissue_style_type == 0 then
        return data
    end

    for i = 0, #appearance.tissue_style_type - 1 do
        local style_type_id = appearance.tissue_style_type[i]
        local tissue_style = appearance.tissue_style[i]
        local length = appearance.tissue_length[i]

        -- Skip invalid entries
        if style_type_id >= 0 and length >= 0 then
            local tissue_name = get_tissue_name(style_type_id, caste_raw)
            local style_name = get_style_name(tissue_style)
            local length_desc = length_to_desc(length)

            table.insert(data, {
                tissue = tissue_name,
                length = length,
                length_description = length_desc,
                style = style_name
            })
        end
    end
    return data
end

-- Get equipment data
local function get_equipment(unit)
    local data = {
        worn = {},
        wielded = {},
        carried = {}
    }

    if not unit.inventory or #unit.inventory == 0 then
        return data
    end

    for i = 0, #unit.inventory - 1 do
        local inv_item = unit.inventory[i]
        if inv_item and inv_item.item then
            local item = inv_item.item
            local item_name = dfhack.items.getDescription(item, 0)
            local mode = inv_item.mode

            -- Try to get dye color from improvements (specifically THREAD improvements)
            local dye_color = nil
            local improvements = item.improvements or item.improvement
            if improvements and #improvements > 0 then
                for i = 0, #improvements - 1 do
                    local imp = improvements[i]
                    if imp then
                        local imp_type = imp:getType()
                        -- Check THREAD improvements for dye compound
                        if imp_type == df.improvement_type.THREAD and imp.dye then
                            if imp.dye.mat_type and imp.dye.mat_type >= 0 then
                                local dye_mat_info = dfhack.matinfo.decode(imp.dye.mat_type, imp.dye.mat_index)
                                if dye_mat_info and dye_mat_info.material then
                                    local dye_mat = dye_mat_info.material
                                    local SOLID = df.matter_state.Solid or 0

                                    -- Try to get color from state_color_str first (most specific)
                                    if dye_mat.state_color_str and dye_mat.state_color_str[SOLID] and dye_mat.state_color_str[SOLID] ~= "" then
                                        dye_color = dye_mat.state_color_str[SOLID]:lower()
                                    -- Then try the color descriptor (this gives us "midnight blue" etc)
                                    elseif dye_mat.state_color and dye_mat.state_color[SOLID] then
                                        local color_id = dye_mat.state_color[SOLID]
                                        if color_id >= 0 and color_id < #df.global.world.raws.descriptors.colors then
                                            local color_desc = df.global.world.raws.descriptors.colors[color_id]
                                            if color_desc and color_desc.name and color_desc.name ~= "" then
                                                dye_color = color_desc.name:lower()
                                            end
                                        end
                                    -- Finally try state_adj as fallback
                                    elseif dye_mat.state_adj and dye_mat.state_adj[SOLID] and dye_mat.state_adj[SOLID] ~= "" then
                                        dye_color = dye_mat.state_adj[SOLID]:lower()
                                    end

                                    -- If we found a color, break out
                                    if dye_color then
                                        break
                                    end
                                end
                            end
                        end
                    end
                end
            end

            -- Add dye info to the item name if found (exclude generic colors)
            if dye_color and dye_color ~= "" and dye_color ~= "white" and dye_color ~= "gray" then
                item_name = item_name .. " (dyed " .. dye_color .. ")"
            end

            -- Categorize by mode using lookup table
            local category = EQUIPMENT_CATEGORIES[mode]
            if category == "worn" then
                table.insert(data.worn, item_name)
            elseif category == "wielded" then
                table.insert(data.wielded, item_name)
            elseif category == "other" then
                table.insert(data.carried, item_name)
            end
        end
    end
    return data
end

-- ============================================================================
-- MAIN EXECUTION
-- ============================================================================

-- Get the selected unit
local unit = dfhack.gui.getSelectedUnit()
if not unit then
    qerror("No unit selected!")
end

-- Get basic unit info
local race_raw = df.global.world.raws.creatures.all[unit.race]
local caste_raw = race_raw.caste[unit.caste]
local appearance = unit.appearance

-- Collect all data
local payload = {
    race = race_raw.creature_id,
    caste = caste_raw.caste_id,
    sex = caste_raw.sex,
    body_modifiers = get_body_modifiers(appearance, caste_raw),
    bp_modifiers = get_bp_modifiers(appearance, caste_raw),
    color_modifiers = get_color_modifiers(appearance, caste_raw),
    tissue_styles = get_tissue_styles(appearance, caste_raw),
    equipment = get_equipment(unit)
}

-- Print to console (optional, but good for verification)
print(json.encode(payload))

-- Send to API
local json_str = json.encode(payload)

print("Sending data to " .. API_URL .. "...")

-- Parse API_URL to get host and port
local protocol, domain, port_str, url_path = API_URL:match("^(http://)([^:/]+):?(%d*)(.*)")
if not protocol then
    -- try without protocol
    domain, port_str, url_path = API_URL:match("^([^:/]+):?(%d*)(.*)")
end

if not domain then
    print("Invalid API URL")
    return
end

local port = tonumber(port_str) or 80
if url_path == "" then url_path = "/" end

local client = luasocket.tcp:connect(domain, port)
if client then
    client:setTimeout(30)
    local request = "POST " .. url_path .. " HTTP/1.1\r\n" ..
                    "Host: " .. domain .. "\r\n" ..
                    "Content-Type: application/json\r\n" ..
                    "Content-Length: " .. #json_str .. "\r\n" ..
                    "Connection: close\r\n" ..
                    "\r\n" ..
                    json_str

    client:send(request)
    
    -- Read status line
    local status_line, err = client:receive("*l")
    if status_line then
        print("Server responded: " .. status_line)
        -- Read the rest
        local body, err = client:receive("*a")
        if body then
            print("Response body received (" .. #body .. " bytes)")
        else
            print("Error reading body: " .. tostring(err))
        end
    else
        print("Error reading status line: " .. tostring(err))
    end

    client:close()
    print("\nData sent successfully!")
else
    print("\nFailed to connect to API.")
end
