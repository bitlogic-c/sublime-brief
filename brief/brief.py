import sublime
import sublime_plugin


class ExampleCommand(sublime_plugin.TextCommand):             
    def run(self, edit, key ):

        line_move = dict( up = -1, down = 1 )

        # self.view.insert(edit, 0, "Hello, Chester!")
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

    def on_query_context(self, key, operator, operand, match_all):
        print( key, operator, operand, match_all )
        return None
