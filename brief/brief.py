import sublime
import sublime_plugin
from sublime import Region
import datetime
import logging
import sys
import functools

logger = logging.getLogger( __name__ )
logger.setLevel( logging.INFO )

logging.basicConfig( stream=sys.stdout)


MODE = ['column','line','block','off']
MOVE_KEYS = ['right','left','up','down']

class ExampleCommand(sublime_plugin.TextCommand):             
    
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.selection_mode = "off"
        self.curr_point = None
        print( sys.version )

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
        self.view.show(line, False)
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
                dx = self.view.em_width()
                dy = self.view.line_height()

                selection = self.view.sel()
                top_left = selection[0].begin()
                bottom_right = selection[-1].end()
                lines = self.view.lines( sublime.Region(top_left,bottom_right))
                if key == 'right':
                    right_layouts = list(map( lambda y: Region( self.view.layout_to_text(y[0]), self.view.layout_to_text(( y[1][0] + dx, y[1][1] ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                    selection.add_all(right_layouts)
                elif key == 'left':
                    right_layouts = list(map( lambda y: Region( self.view.layout_to_text(( y[0][0] - dx, y[0][1] )), self.view.layout_to_text(( y[1][0], y[1][1] ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                    selection.add_all(right_layouts)
                elif key == 'up':
                     right_layouts = list(map( lambda y: Region( self.view.layout_to_text(( y[0][0], y[0][1] - dy )), self.view.layout_to_text(( y[1][0], y[1][1] - dy ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                     selection.add_all(right_layouts)
                elif key == 'down':
                     right_layouts = list(map( lambda y: Region( self.view.layout_to_text(( y[0][0], y[0][1] + dy )), self.view.layout_to_text(( y[1][0], y[1][1] + dy ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                     selection.add_all(right_layouts)
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
