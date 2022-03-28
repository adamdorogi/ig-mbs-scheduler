SELECT_FILES_SCRIPT = """on run {media_dir_path}
    tell application "System Events"
        activate application "Brave Browser"
        
        -- Wait for file selection dialog
        repeat until exists sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser")
        end repeat
        
        -- Open file search dialog
        keystroke "g" using {command down, shift down}
        
        -- Wait for search input to appear, and enter folder path
        repeat until exists combo box "Go to the folder:" of sheet 1 of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser")
        end repeat
        set value of combo box "Go to the folder:" of sheet 1 of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser") to media_dir_path
        
        -- Wait for "Go" button to appear, and click
        repeat until exists button "Go" of sheet 1 of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser")
        end repeat
        click button "Go" of sheet 1 of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser")
        
        -- Wait for search input to disappear
        repeat until not (exists sheet 1 of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser"))
        end repeat
        
        -- Move to folder of choice and select all files
        key code 124 -- right arrow key
        keystroke "a" using command down
        
        -- Open selected files
        click button "Open" of sheet 1 of window "Meta Business Suite - Brave" of (first process where frontmost is true and name is "Brave Browser")
    end tell
end run"""
