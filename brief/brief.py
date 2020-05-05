import sublime
import sublime_plugin
from sublime import Region
import datetime
import logging
import sys
import functools
import io

logger = logging.getLogger( __name__ )
logger.setLevel( logging.INFO )

logging.basicConfig( stream=sys.stdout)


class Selection(list):
    def __init__(self, regions ):
        self.extend(regions)

    def __str__(self):
        buff = io.StringIO()
        for curr in self:
            buff.write( "({},{},{})".format(curr.begin(), curr.end(), curr.xpos) )
        return "[{}]".format(buff.getvalue())



MODE = ['column','line','block','off']
MOVE_KEYS = ['right','left','up','down']

class ExampleCommand(sublime_plugin.TextCommand):             
    
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.selection_mode = "off"
        self.cursor = None
        self.dx = self.view.em_width()
        self.dy = self.view.line_height()
        

    def _move(self, edit, key ):
        selection = self.view.sel()
        self.cursor = self.view.text_to_layout( selection[0].begin() )
        self.cursor = ( max(self.cursor[0],selection[0].xpos), self.cursor[1] )
        selection.clear()
        if key == 'left':
            pos = self.view.layout_to_text(self.cursor)
            self.cursor = self.view.text_to_layout(pos)
            self.cursor = ( self.cursor[0] - self.dx, self.cursor[1] )
            pos = self.view.layout_to_text(self.cursor)
            selection.add(Region( pos, pos, self.cursor[0] ))
        elif key == 'right':
            self.cursor = ( self.cursor[0] + self.dx, self.cursor[1] )
            pos = self.view.layout_to_text(self.cursor)
            new_layout = self.view.text_to_layout(pos)
            self.cursor = ( new_layout[0], new_layout[1] ) 
            selection.add(Region( pos, pos, self.cursor[0] ))
        elif key == 'up':
            self.cursor = ( self.cursor[0], self.cursor[1] - self.dy)
            pos = self.view.layout_to_text(self.cursor)
            selection.add(Region( pos, pos, self.cursor[0] ))
        elif key == 'down':
            self.cursor = ( self.cursor[0], self.cursor[1] + self.dy)
            pos = self.view.layout_to_text(self.cursor)
            selection.add(Region( pos, pos, self.cursor[0] ))

        self.view.show(selection[0], False)    
         


    def run(self, edit, key ):
        print( Selection(list(self.view.sel())) )
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
                    self.cursor = ( self.cursor[0] + self.dx, self.cursor[1] )
                    right_layouts = list(map( lambda y: Region( self.view.layout_to_text(y[0]), self.view.layout_to_text(( y[1][0] + dx, y[1][1] ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                    selection.add_all(right_layouts)
                elif key == 'left':
                    self.cursor = ( self.cursor[0] - self.dx, self.cursor[1] )
                    right_layouts = list(map( lambda y: Region( self.view.layout_to_text(( y[0][0], y[0][1] )), self.view.layout_to_text(( y[1][0] - dx, y[1][1] ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ] ))
                    selection.clear()
                    selection.add_all(right_layouts)
                elif key == 'up':
                     right_layouts = list(map( lambda y: Region( self.view.layout_to_text(( y[0][0], y[0][1])), self.view.layout_to_text(( y[1][0], y[1][1] ))), 
                                               [ (self.view.text_to_layout( x.begin() ), self.view.text_to_layout( x.end() )) for x in selection ][:-1] ))
                     selection.clear()
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
                    self.cursor = self.view.text_to_layout( selection[0].begin() )
                    point = selection[0].a
                    line = self.view.full_line(point)

                    selection.clear()
                    selection.add( line )
                else:
                    self.selection_mode = 'off'
            elif key == 'block':
                selection = self.view.sel()
                if self.selection_mode == 'off':
                    self.selection_mode = 'block'
                    self.cursor = self.view.text_to_layout( selection[0].begin() )
                    point = selection[0].a
                    selection.clear()
                    selection.add( sublime.Region(point,point) )
                else:
                    self.selection_mode = 'off'
                    point = selection[0].b
                    selection.clear()
                    selection.add( sublime.Region(point,point) )
            elif key == 'column':
                selection = self.view.sel()
                if self.selection_mode == 'off':
                    self.selection_mode = 'column'
                    self.cursor = self.view.text_to_layout( selection[0].begin() )
                    point = selection[0].a
                    layout = self.view.text_to_layout(point)
                    selection.clear()
                    selection.add( sublime.Region(point,point,layout[0]) )
                else:
                    self.selection_mode = 'off'
                    point = selection[0].b
                    selection.clear()
                    selection.add( sublime.Region(point,point) )



        logger.info( "{} Processing..Key: {} Mode: {} Selection: {} LastCommand: {}".format(datetime.datetime.now(), key, self.selection_mode, Selection(list(self.view.sel())),
                                                                                                                                                self.view.command_history(0) ) )
            






    def on_query_context(self, key, operator, operand, match_all):
        print( key, operator, operand, match_all )
        return None
