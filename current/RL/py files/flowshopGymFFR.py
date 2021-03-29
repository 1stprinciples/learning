# THis is the flowshopGym class with the Fast Forwarded Reward (FFR) implemented


class flowshopGym:
    import random
    # --------------------------------------INITIALIZE THINGS------------------------------------------
    def __init__(self):
        self.NUM_PRODUCTS = 200
        self.IAT = 0.001 # change this to sample from some distribution
        self.action_space = gym.spaces.Discrete(3)
        self.DEBUG = 1 # 1 = check simpy env ; 2 = check the openai processes
        #self.observation_space = gym.spaces.Discrete(9)
        # Rich observation space
        # Product type for the 4 product type, time left for the 4 products, product type in machine
        # For more details Thesis notes book on Notability
        self.observation_space = gym.spaces.Tuple((
                                                  gym.spaces.Discrete(3),gym.spaces.Discrete(3), # MC1 Queue prod type
                                                  gym.spaces.Discrete(3),gym.spaces.Discrete(3),
                                                  gym.spaces.Discrete(11),gym.spaces.Discrete(11), # MC1 Queue time left 
                                                  gym.spaces.Discrete(11),gym.spaces.Discrete(11),
                                                  gym.spaces.Discrete(3), # MC1 prod type
                                                  ))
        
        
        
        #self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.prod_and_requests = []
        self.machine_production = 0
        self.reward = 0 
        self.cumulative_reward = 0 
        self.machine1_prev_type = 0 # The previous product type in the machine
        self.QUEUE_LENGTH = 4
        self.DDF = 4
        self.metadata = []
        
        # The following two values from the setup time matrix
        self.P1_to_P2 = 10
        self.P2_to_P1 = 20
        
        # The range for the time converter
        self.TIME_MAX = 4000
        self.TIME_MIN = -4000
        
        self.state_format = 'Hosp'
    # --------------------------------------DEFINE PROCESSES------------------------------------------
    
    # Process 1 - Spawn of products
    def process_1(self):
        #print("Entered new product process")
        
        # Produce X number of products
        for i in range(self.NUM_PRODUCTS):
            
            # Creating instances of the product 
            ###print("creating instance", i)
            self.instances.append(self.product(self,self.envSimpy,'Product_%d' % i, self.store, self.machine))
            
            # IAT TIMEOUT BEFORE THE NEXT SPAWN
            #next_admission = random.expovariate(1 / interarrival_time)
            yield self.envSimpy.timeout(self.IAT)
        
        # After all the products are put into the store, start process 2
        # Process 2 - Getting products from the store and create machine request
        self.envSimpy.process(self.process_2())
    
    class product(object):
        def __init__(self, flowshopGym, envSimpy, name, number, machine):
            
            # Creating the required resources and environment
            self.envSimpy = envSimpy

            # State space variables
            self.prod_type = random.randint(1,2) # the product type of the product.
            self.production_time = 15
            
            
            # Rest of the variables
            
            # Using the method that Thomas said in rocketchat - TWK method
            # Formula is start time + sum of processing times * due date factor 
            # Due date factor is generally 3
            sim.TWK = self.envSimpy.now + self.production_time * sim.DDF # Total Work Content (TWK)
            self.production_end = sim.TWK
            #self.production_end = random.randint(np.ceil(self.envSimpy.now), np.ceil(TWK))
            self.name = name
            self.number = number
            self.machine = machine 
            
            ###print(self.name,"created")
            
            # putting the product into the store
            self.envSimpy.process(self.put_store())
            
 

        def put_store(self): # I am putting 
            yield sim.envSimpy.timeout(1)
            ###print("Putting the", self.name, "in the store at", self.envSimpy.now)
            yield sim.store.put(self)
            ###print("Items in the store",len(sim.store.items)," - time -",self.envSimpy.now)
            
        
    
    
    # -----------------------------PROCESS 2-------------------------------------------------  
    def process_2(self): # If machine.queue is less than 4, get a prod from store and create request
        while True:
            if len(self.machine.queue) < self.QUEUE_LENGTH:
                
                # Get product from store
                prod = yield self.store.get()
                
                TWK = self.envSimpy.now + prod.production_time * self.DDF # Total Work Content (TWK)
                prod.production_end = TWK
                # Request machine
                ###print("requesting machine for", prod.name)
                req = prod.machine.request()
                
                self.envSimpy.process(self.process_3(prod, req))
            else:
                yield self.envSimpy.timeout(1)
    
    def calc_setup_time(self, prod):
        #Setup process if required
        #returns the setup time

        #print("setup time ### ",self.machine1_prev_type , prod.prod_type, "at", self.envSimpy.now )
        if self.machine1_prev_type == 0:
            ###print("Previous machine type was 0")
            return 0 # dont' do anything during the first pass
        elif self.machine1_prev_type == prod.prod_type:
            ###print("Same product type between MC and incoming product")
            return 0 # Dont' do anything if the product types are the same 
        elif prod.prod_type == 2: # current product type = 2 meaning we have to do a changeover from 1 to 2
            ###self.reward = self.reward - 5 # -ve reward when there is a setup change
            return self.P1_to_P2
            ###print("Setup time prod1 to prod2 finished at",self.envSimpy.now )
        elif prod.prod_type == 1: # current product type = 1 meaning we have to do a changeover from 2 to 1
            ###self.reward = self.reward - 5 # -ve reward when there is a setup change
            return self.P2_to_P1
            ###print("Setup time prod2 to prod1 finished at",self.envSimpy.now )
        else:
            raise Exception("Sorry product type doesn't match available values [for Setup process]")
        
    # -----------------------------PROCESS 3-------------------------------------------------  
    def process_3(self,prod, req): # Wait for req to go through and then produce and release the machine  
        sim.prod_and_requests.append([prod,req])
        # Wait for the request to succeed
        yield req
        
        # Fast Forwarding reward
        setup_time = self.calc_setup_time(prod)
        production_start = self.envSimpy.now
        projected_production_end = production_start + setup_time + prod.production_time
        prod.tardiness = projected_production_end - prod.production_end # actual end time - deadline 
        self.info['Tardiness'] = prod.tardiness
        #print("Prod start, setup, production_time, tardiness",production_start, setup_time, 
              #prod.production_time, prod.tardiness)
        
        # Decide the reward 
        #if prod.tardiness <= 0:
        #    sim.reward = sim.reward + 10 
        #else: 
        #    sim.reward = sim.reward + 0
        if prod.tardiness <=0:
            sim.reward = sim.reward +  (-1 * prod.tardiness)
        else:
            sim.reward += 0            
        yield self.envSimpy.timeout(setup_time)
        #print("Time after setup time", self.envSimpy.now)
        
        # ----------------------------
        ###print('Start production of ' + str(prod.name) + ' at '+ str(self.envSimpy.now)  )

        ###print("Production time", prod.production_time)
        self.machine_production = 1
        yield self.envSimpy.timeout(prod.production_time)
        ###print('Production finished at' + str(self.envSimpy.now))
        
        # Changing the previous prod_type on the machine
        self.machine1_prev_type = prod.prod_type
        
        #prod.tardiness = self.envSimpy.now - prod.production_end   # -ve is good; +ve is bad 
        
        #self.info['Tardiness'] = prod.tardiness
        # End of production 
        #print('End production of ' + str(prod.name) + ' at ' + str(self.envSimpy.now))


        # Wait for an acceptance only when there are products in the machine.queue
        if len(sim.machine.queue) != 0:
            self.machine_production = 0
            # 1. After production pass the time so that the agent can take action based on the latest state
            # 2. Pass time when the action chosen by the agent is rejection
            i = 0
            while True:
                if i == 0:
                    yield self.envSimpy.timeout(1)
                    #print("Timeout after production")
                i += 1

                
                ###print("Initial queue", sim.machine.queue)
                ###print("Initial queue LENGTH", len(sim.machine.queue))
                ###print("Current_action", sim.current_action)

                if sim.current_action == 1: #rejected

                    # rearrange the machine queue to reflect the rejection
                    sim.machine.queue.insert(len(sim.machine.queue), sim.machine.queue.pop(0))
                    ###print("Resultant queue",sim.machine.queue)
                    ###print("\n")
                    #print("Action rejected; Passing time by 1 ", i)
                    #print("Machine queue,prod types ", sim.machine.queue, sim.getObs())
                    #print("Current time " + str(self.envSimpy.now))
                    #print("Machine product type ",)
                    #print("Queue item 1 product type ", )
                    yield self.envSimpy.timeout(1)




                    # rearrange the machine queue to reflect the rejection
                    #self.machine.queue.insert(len(self.machine.queue), self.machine.queue.pop(0))


                    # print the rearranged machine queue
                    #print('#observation_after')
                    #print(envGym.getObservation())



                elif sim.current_action == 0: #if action accepted
                    ###print("Resultant queue",sim.machine.queue)
                    
                    ###print('\n')
                    break
                elif sim.current_action == 2: # do nothing action
                    #sim.reward = sim.reward - 5 
                    yield self.envSimpy.timeout(1)
        else:
            pass


        

        #print("Tardiness is ",prod.tardiness)
        # Production has ended now I have to take the next action using take_action()
        # envGym.machine.queue = envGym.take_action()
        #envGym.machine.queue = []

        # Release the machine
        #yield prod.machine.release(req)
        
        # Release the machine
        yield prod.machine.release(req)

        # timeout before the next check
        #yield env.timeout(1)
    # ----------------------------------------------------------------------------------------------
    # --------------------------------------DEFINE FUNCTIONS------------------------------------------
    # ----------------------------------------------------------------------------------------------
    
    def getObs(self): 
        # CREATING TUPLE/DICT TO HOLD INFO        
        test_state = dict()
        
        # Machine 1 product type - Initial value
        test_state['MC1_prod_type'] = 0
        # Machine 1 queue product type - Initial values
        test_state['MC1_queue1_type'] = 0
        test_state['MC1_queue2_type'] = 0
        test_state['MC1_queue3_type'] = 0
        test_state['MC1_queue4_type'] = 0 
        # Machine 1 queue time left - Initial values
        test_state['MC1_queue1_timeleft'] = 0
        test_state['MC1_queue2_timeleft'] = 0
        test_state['MC1_queue3_timeleft'] = 0
        test_state['MC1_queue4_timeleft'] = 0
        
        # 1. PRODUCT TYPE INSIDE THE MACHINE
        if len(sim.machine.users) != 0: #if the machine is not empty
            test_state['MC1_prod_type'] = (self.relater(sim.machine.users[0])).prod_type # Product type of the product inside machine 1
        else:
            pass # No product inside the machine
        
        
        # 2. PRODUCT TYPE IN MACHINE 1 QUEUE
        if len(sim.machine.queue) == 0: # queue is empty
            pass # Already defined these values while creating the dict()

        elif len(sim.machine.queue) == 1:
            # Machine 1 queue1 product type
            test_state['MC1_queue1_type'] = (self.relater(sim.machine.queue[0])).prod_type
            
        elif len(sim.machine.queue) == 2:
            # Machine 1 queue1 product type
            test_state['MC1_queue1_type'] = (self.relater(sim.machine.queue[0])).prod_type
            
            # Machine 1 queue2 product type
            test_state['MC1_queue2_type'] = (self.relater(sim.machine.queue[1])).prod_type
        
        elif len(sim.machine.queue) == 3:
            # Machine 1 queue1 product type
            test_state['MC1_queue1_type'] = (self.relater(sim.machine.queue[0])).prod_type
            
            # Machine 1 queue2 product type
            test_state['MC1_queue2_type'] = (self.relater(sim.machine.queue[1])).prod_type
            
            # Machine 1 queue3 product type
            test_state['MC1_queue3_type'] = (self.relater(sim.machine.queue[2])).prod_type
        
        elif len(sim.machine.queue) == 4:
            # Machine 1 queue1 product type
            test_state['MC1_queue1_type'] = (self.relater(sim.machine.queue[0])).prod_type
            
            # Machine 1 queue2 product type
            test_state['MC1_queue2_type'] = (self.relater(sim.machine.queue[1])).prod_type
            
            # Machine 1 queue3 product type
            test_state['MC1_queue3_type'] = (self.relater(sim.machine.queue[2])).prod_type
            
            # Machine 1 queue4 product type
            test_state['MC1_queue4_type'] = (self.relater(sim.machine.queue[3])).prod_type
        
        else:
            raise Exception("Queue length incompatible")

        
        # 3. TIME LEFT CALCULATION
        # for each position
        if test_state['MC1_queue1_type'] != 0: # product present
            time_left = self.time_left((self.relater(sim.machine.queue[0])).production_end)
            test_state['MC1_queue1_timeleft'] = self.time_convert(time_left)
                
        if test_state['MC1_queue2_type'] != 0: # product present
            time_left = self.time_left((self.relater(sim.machine.queue[1])).production_end)
            test_state['MC1_queue2_timeleft'] = self.time_convert(time_left)
        
        if test_state['MC1_queue3_type'] != 0: # product present
            time_left = self.time_left((self.relater(sim.machine.queue[2])).production_end)
            test_state['MC1_queue3_timeleft'] = self.time_convert(time_left)
        
        if test_state['MC1_queue4_type'] != 0: # product present
            time_left = self.time_left((self.relater(sim.machine.queue[3])).production_end)
            test_state['MC1_queue4_timeleft'] = self.time_convert(time_left)
            
        obs = [v for k,v in test_state.items()]    
        #print("------ obs ", tuple(obs))
        
        return tuple(obs)
    
    def time_left(self, due):
        #print("due, time now", due, sim.envSimpy.now)
        return (due - sim.envSimpy.now)
    
    def time_convert(self, time):
        #print("Time to convert",time)
        time_max = self.TIME_MAX
        time_min = self.TIME_MIN
        
        if time_min < time <= time_max:
            min_max_time = (time-time_min)/(time_max-time_min)
            scaled_time = min_max_time * 10 # Scaling time to be between 0 and 20
            return int(np.ceil(scaled_time))
        else:
            raise Exception("Input time value outside range in def time_convert")
    
     
    def encode(self, obs):
        #print('Entered encode')
        # (3), 3 [Machine queue type, machine product type]
        i = obs[0] 
        i *= 3
        
        i += obs[1]
        #print("Value of i inside encode ", i)
        return i
    
    def doneFn(self):
        # So the condition is, 
        #(no items in queue1 + queue2 + ...) AND 
        #(no machine is running)
        if self.machine.queue != None:
            lenQueue = len(self.machine.queue)
        else: 
            lenQueue = 0 
        lenMachinesUsed = self.machine.count
        #print("Queue length",lenQueue, "no machines used", lenMachinesUsed)
        # (self.relater(self.machine.queue[-1]).production_end)*2
        if (self.envSimpy.now) > 3500: # Early break if time crosses the TWK; Breaking 3 time steps early
            self.early_break = True
        else:
            self.early_break = False

        if (lenQueue == 0 and lenMachinesUsed == 0) or (self.early_break == True) :
            #print("length of queue ",lenQueue,"Machines used ", lenMachinesUsed)
            #print("###now, TWK", self.envSimpy.now, self.TWK)
            return True
        else:
            #print("length of queue ",lenQueue,"Machines used ", lenMachinesUsed)
            return False

    
    # A function to relate products and requests
    def relater(self,item):
        # Note that the input to this function shouldn't be a list. It should be of 
        # type request or product
        #print("Entered relater with this item ###", item, type(item))
        output_item = None
        
        if str(type(item)) != "<class '__main__.flowshopGym.product'>" and str(type(item)) != 'simpy.resources.resource.Request':
            raise Exception("Passed in a list to relater. Expecting request or product object")
            #print("Error passed in a list. Expecting request or product object")
            return None
        # If the input is a request
        #print("self.prod_and_requests", self.prod_and_requests)
        if type(item) == simpy.resources.resource.Request:
            for i, j in enumerate(self.prod_and_requests):
                if j[1] == item:
                    output_item = j[0]
                    return output_item
        else: #if the input is a product 
            for i, j in enumerate(self.prod_and_requests):
                if j[0] == item:
                    output_item = j[1]
                    return output_item   
    
    
    # --------------------------------------RENDER------------------------------------------
    
    
    
    
    # --------------------------------------RESET------------------------------------------
    def reset(self):
        #print("Entered Reset")
        # Initialise simpy environemnt and a machine
        self.envSimpy = simpy.Environment()
        self.machine = simpy.Resource(self.envSimpy,capacity = 1)
        self.store = simpy.Store(self.envSimpy) 
        
        # Initial variable definitions
        self.time_start = self.envSimpy.now
        self.next_time_stop = self.time_start + 1
        self.time_step = 1
        self.time_step_terminal = self.time_start + 100
        self.current_action = 0
        self.instances = []
         
        # Set up starting processes
        self.envSimpy.process(self.process_1())
        
        # Set starting state values

        
        # Inital load of patients (to average occupancy)
        #self._load_patients()
        
        # Starting values of observations
        observations = self.getObs()
        
        # Put state dictionary items into observations list (Define observations)
        #observations = [v for k,v in self.state.items()]
        return observations
    
    
    
    
    # --------------------------------------STEP------------------------------------------
    
    def step(self, action):
        
        # Define params
        self.current_action = action
        self.action_taken = False 
        self.info = {}
        self.reward = 0 
        
        # Reward based on the production status
        #if self.machine_production == 1:  
        #    self.reward = -1 # a simple negative reward when the machine is waiting for a decision 
        #    if self.current_action == 0 or self.current_action == 1: # action is accepted or rejected
        #        self.reward = self.reward -20
        #        print("### wrong action")
        
        #print("machine is used by",sim.machine.users)
        #print("machine production status", self.machine_production)
        #print("Agent action", action)
        # Run for time_step
        self.next_time_stop += self.time_step
        self.envSimpy.run(until = self.next_time_stop)
        
        
        
        # Get values
        observation = self.getObs()
        done = self.doneFn()
        
        
        # each step has a -1 reward 
        #self.reward = self.reward - 1 
        

        
        if done == True and self.early_break != True:
            self.reward = self.reward + 50 # Very high reward for completing all jobs
        info = self.info
        self.cumulative_reward += self.reward
        #print("Values from Step",observation, sim.reward, done, info)
        # Return values
        return (observation, self.reward, done, info)

        
    