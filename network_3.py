import queue
import threading
import ast

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)


## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths
    dst_S_length = 5
    prot_S_length = 1
    change_bit_length = 1

    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, change_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        self.change_S = change_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.change_S
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length ]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        change_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length + NetworkPacket.change_bit_length]
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length + NetworkPacket.change_bit_length : ]
        return self(dst, prot_S, change_S, data_S)




## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination

    ## called when printing the object
    def __str__(self):
        return self.addr

    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, change_S, data_S):
        p = NetworkPacket(dst, 'data', change_S, data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return



## Implements a multi-interface router
class Router:

    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        #TODO: set up the routing table for connected hosts
        self.rt_tbl_D = self.create_table()# {destination: {router: cost}}
        print('%s: Initialized routing table' % self)
        self.print_routes()

    def create_table(self):
        cost_table = self.cost_D
        table = {self.name:{self.name:0}}
        # {i: [t, n] for t, nd in d.items() for i, n in nd.items()}
        for key, value in cost_table.items():
            table.update({key:{}})
            for k, v in value.items():
                table[key].update({self.name:v})
        return table

    '''## Print routing table
    def print_routes(self):
        # rows = len(self.rt_tbl_D.items())
        # print(rows)
        #TODO: print the routes as a two dimensional table
        # print(self.cost_D)
        print(self.rt_tbl_D)'''
    ## Print routing table
    def print_routes(self):
        print(self.rt_tbl_D)
        key=list(self.rt_tbl_D.keys()) # list of all destinations
        routers=[] #initializes a list of all routers
        for dest in key: #finds all routers
            for i in self.rt_tbl_D[dest]:
                if i not in routers:
                    routers.append(i)

        key_name="|"+str.ljust(self.name,4)+"|"   #title of table (ie what router we are viewing its table)
        header="======"
        if len(key)>=1:
            for i in key:
                key_name+=str.rjust(i,4)+"|"
                header+="====="
            full=header+"\n"+key_name+"\n"+header+"\n"
            #print(header)   #correct length dashed line
            #print(key_name)  #list of all routers/destinations
            #print(header)
            for i in routers:
                node_str="|"
                for j in key:
                    try:
                        node_str+=str.rjust(str(self.rt_tbl_D[j][i]),4)+"|"   #distance from router to destination
                    except:
                        node_str+="none|"    #no route exists yet
                full+="|"+str.ljust(i,4)+node_str+"\n"
                full+=header+"\n"
            print(full)
            #print(self.rt_tbl_D)



    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))


    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            # print("Cost table " + str(self.cost_D))
            dest = p.dst
            if dest not in self.cost_D:
                route = self.rt_tbl_D[dest]
                #print(route)
                #print(self.cost_D)
                cost=9999
                for a,b in route.items():
                    if a in self.cost_D and cost>b:
                        cost=b
                        router = a
                        for intf, cost in self.cost_D[router].items():
                            interface=intf
                    if a in self.cost_D and cost==b:
                        cost=9999
                        for intf, temp_cost in self.cost_D[a].items():
                            if int(temp_cost)<cost:
                                cost=int(temp_cost)
                                interface=intf
                print(router, "at cost:",cost)
                    #elif a in self.cost_D and cost==b:
                        #if
                #print("Router is " + str(router))
                #print(self.cost_D)

                #interface = intf #Router -> interface
                print("Interface " + str(interface))
            # if dest in self.rt_tbl_D:
            #     print("Dest is " + str(dest))
            #     for key,value in self.rt_tbl_D[dest].items():
            #         router = self.rt_tbl_D[key]
            #         # print("Router is " + str(router))
            #         for k,v in router.items():
            #             if k in self.cost_D:

            #                 print("Cost table " + str(k))
                    # print("Router is " + str(router))
                self.intf_L[interface].put(p.to_byte_S(), 'out', True)
                print('%s: forwarding packet "%s" from interface %d to %d' % \
                    (self, p, i, 0))
            else:
                for intf, cost in self.cost_D[dest].items():
                    interface = intf
                    self.intf_L[interface].put(p.to_byte_S(), 'out', True)
                    print('%s: forwarding packet "%s" from interface %d to %d' % \
                        (self, p, i, 1))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        #create a routing table update packet
        p = NetworkPacket(i, 'control', '1', str(self.rt_tbl_D))
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #dx(y) = minv{c(x,v) + dv(y)} Bellman-Ford Equation
        routes_changed=False
        table = ast.literal_eval(p.data_S)
        if p.change_S == '1':
            for dest, value in table.items():
                for router, dist in value.items():

                    if dest not in self.rt_tbl_D:
                        get_cost = self.rt_tbl_D[router]
                        for c,d in get_cost.items():
                            added_cost = int(d)
                        self.rt_tbl_D.update({dest:{router:(dist+added_cost)}})
                        routes_changed=True
                        #self.rt_tbl_D[dest].update({c:added_cost+self.rt_tbl_D[router][c]})
                        self.update_routes(p,i)
                        return 0
                    elif dest == self.name or dest == router:
                        pass
                    else:
                        for k,v in self.rt_tbl_D[dest].items():
                            if v > int(dist) and router==k:                # updates table if it finds a cheaper cost
                                self.rt_tbl_D[dest].update({router:dist})
                                routes_changed=True
                        if router not in self.rt_tbl_D[dest]:      # updates table with alternate paths to destinations
                            self.rt_tbl_D[dest].update({router:dist})
                            routes_changed=True

            destinations=[]
            for dest, paths in self.rt_tbl_D.items():
                destinations.append(dest)
            for dest in destinations:  #for all destinations (top row)
                for router in destinations:   #for each router (left axis)
                    if router==dest and router[0].upper()=="R":
                        self.rt_tbl_D[dest].update({router:0})
                    elif router[0].upper()=="R":   #if no path from router to dest
                        for alt in destinations:
                            try:
                                dist=self.rt_tbl_D[dest][router]   #cheapest known path is what is in the table
                            except:                                #or really high number if it isn't
                                dist=9999
                            if alt in self.rt_tbl_D[dest] and alt in self.rt_tbl_D[router] and dist>self.rt_tbl_D[dest][alt]+self.rt_tbl_D[router][alt]:  # if we can get to dest with a step to alt that is cheaper
                                dist=self.rt_tbl_D[dest][alt]+self.rt_tbl_D[router][alt]
                            self.rt_tbl_D[dest].update({router:dist})


            p.change_S = '0'
            if routes_changed:     # if the table is changed, it will send an updated table out to all interfaces
                i=0
                for _ in self.intf_L:
                    self.send_routes(i)
                    i+=1
        else:
            # p.change_S = '0'
            pass

        #TODO: add logic to update the routing tables and
        # possibly send out routing updates

        self.print_routes()
        print('%s: Received routing update %s from interface %d' % (self, p, i))


    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
