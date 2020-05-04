import sublime
import sublime_plugin
import datetime
import logging
import sys
import functools

logger = logging.getLogger( __name__ )
logger.setLevel( logging.INFO )

logging.basicConfig( stream=logging.StreamHandler(sys.stdout) )


MODE = ['column','line','block','off']
MOVE_KEYS = ['right','left','up','down']

class ExampleCommand(sublime_plugin.TextCommand):             
    
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.selection_mode = "off"
        self.curr_point = None

    def _move(self, edit, key ):
        line_move = dict( up = -1, down = 1 )

        selection = self.view.sel()
        point = selection[0].a
        x,y = self.view.rowcol(point)
        
        if key in line_move:  
            point = self.view.text_point( x+line_move.get(key,0), 0 )
        else:
            point += dict( right = 1, left = -1 ).get( key, 0 ) 


        selection.clear()
        line = self.view.full_line(point)
        if key in line_move:
            if line.contains( point + y ):
                line.a = line.b = line.a + y
            else:
                line.a = line.b
        else:
            line.a = line.b = point
        
        selection.add( line )   
        # selection.add( sublime.Region( 0, 5) )   

    def run(self, edit, key ):
        if self.view.command_history(0)[0] in [ 'copy', 'right_delete', 'delete','cut']:
            self.selection_mode = 'off'


        if key in MOVE_KEYS:
            if self.selection_mode == 'line':
                selection = self.view.sel()
                line_regions = [ self.view.lines(x) for x in list( selection ) ]
                rows = [ self.view.rowcol(x.begin())[0] for y in line_regions for x in y ]
                min_row = min(rows)
                max_row = max(rows)
                logger.info( "Min: {} Max: {}".format(min_row, max_row))
                if key == 'down':
                    selection.add( self.view.full_line( self.view.text_point(max_row+1, 0 ) ))
                elif key == 'up':
                    selection.add( self.view.full_line( self.view.text_point(min_row-1, 0 ) ))

                region = functools.reduce( sublime.Region.cover, list(selection) )
                selection.clear()
                selection.add(region)
            elif self.selection_mode == 'block':
                selection = self.view.sel()
                region = functools.reduce( sublime.Region.cover, list(selection) )
                selection.clear()
                if key == 'right':
                    region.b += 1
                    selection.add( region )
                elif key == 'left':
                    region.a -= 1    
                    selection.add( region )

                elif key == 'up':
                    point = region.a
                    x,y = self.view.rowcol(point)
                    point = self.view.text_point( x-1, 0 )
                    line = self.view.line(point)
                    if line.contains( point + y ):
                        region.a = point + y
                    else:
                        region.a = point
                    selection.add( region )

                elif key == 'down':
                    point = region.b
                    x,y = self.view.rowcol(point)
                    point = self.view.text_point( x+1, 0 )
                    line = self.view.line(point)
                    if line.contains( point + y ):
                        region.b = point + y
                    else:
                        region.b = line.b
                    selection.add( region )
            elif self.selection_mode == 'column':
                selection = self.view.sel()
                top_left = selection[0].a
                bottom_right = selection[-1].b
                
                lx,ly = self.view.rowcol(top_left)
                rx,ry = self.view.rowcol(bottom_right)

                lines = self.view.lines( sublime.Region(top_left,bottom_right))
                if key == 'right':
                    ry += 1

                    selection.clear()
                    for curr_line in lines:
                        line_section = curr_line.intersection( sublime.Region(curr_line.a + ly, curr_line.a + ry) )
                        selection.add( line_section )
                elif key == 'left':
                    pass
                elif key == 'up':
                    pass
                elif key == 'down':
                    pass
            else:
                self.selection_mode = 'off'
                self._move(edit,key)

        
        elif key in MODE:
            if key == 'line':
                selection = self.view.sel()
                if self.selection_mode == 'off':
                    self.selection_mode = 'line'
                    point = selection[0].a
                    line = self.view.full_line(point)

                    selection.clear()
                    selection.add( line )
                elif self.selection_mode == 'line':
                    self.selection_mode = 'off'
            elif key == 'block':
                selection = self.view.sel()
                if self.selection_mode == 'off':
                    self.selection_mode = 'block'
                    point = selection[0].a
                    selection.clear()
                    selection.add( sublime.Region(point,point) )
                elif self.selection_mode == 'block':
                    self.selection_mode = 'off'
                    point = selection[0].b
                    selection.clear()
                    selection.add( sublime.Region(point,point) )
            elif key == 'column':
                selection = self.view.sel()
                if self.selection_mode == 'off':
                    self.selection_mode = 'column'
                    point = selection[0].a
                    selection.clear()
                    selection.add( sublime.Region(point,point) )
                elif self.selection_mode == 'column':
                    self.selection_mode = 'off'
                    point = selection[0].b
                    selection.clear()
                    selection.add( sublime.Region(point,point) )



        logger.info( "{} Processing..Key: {} Mode: {} Selection: {} LastCommand: {}".format(datetime.datetime.now(), key, self.selection_mode, list(self.view.sel()),self.view.command_history(0) ) )
            






    def on_query_context(self, key, operator, operand, match_all):
        print( key, operator, operand, match_all )
        return None
