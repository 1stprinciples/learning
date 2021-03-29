
print("###Going to import flow shop gym")
import gym
import simpy 
class flowshopGym:
    # --------------------------------------INITIALIZE THINGS------------------------------------------
    def __init__(self):
        self.NUM_PRODUCTS = 20
        self.IAT = 0.001 # change this to sample from some distribution
        self.action_space = gym.spaces.Discrete(2)
        #self.observation_space = gym.spaces.Discrete(9)
        # Rich observation space
        # Product type for the 4 product type, time left for the 4 products, product type in machine
        # For more details Thesis notes book on Notability
        self.observation_space = gym.spaces.Tuple((gym.spaces.Discrete(3), # MC1 prod type
                                                  gym.spaces.Discrete(3),gym.spaces.Discrete(3), # MC1 Queue prod type
                                                  gym.spaces.Discrete(3),gym.spaces.Discrete(3),
                                                  gym.spaces.Discrete(11),gym.spaces.Discrete(11), # MC1 Queue time left 
                                                  gym.spaces.Discrete(11),gym.spaces.Discrete(11)
                                                  ))
        #self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.prod_and_requests = []
        self.reward = 0 
        self.cumulative_reward = 0 
        self.machine1_prev_type = 0 # The previous product type in the machine
        self.QUEUE_LENGTH = 4
        
        # The following two values from the setup time matrix
        self.P1_to_P2 = 5
        self.P2_to_P1 = 4 
        
        # The range for the time converter
        self.TIME_MAX = 200
        self.TIME_MIN = -200
        
        self.state_format = 'Hosp'
    # --------------------------------------DEFINE PROCESSES------------------------------------------
    
    # Process 1 - Spawn of products
    def process_1(self):
        print("Entered new product process")
        
        # Produce X number of products
        for i in range(self.NUM_PRODUCTS):
            
            # Creating instances of the product 
            #self.instances.append(self.product(self,self.envSimpy,'Product_%d' % i,i/100, self.machine))
            self.instances.append(self.product(self,self.envSimpy,'Product_%d' % i, self.store, self.machine))
            
            # IAT TIMEOUT BEFORE THE NEXT SPAWN
            #next_admission = random.expovariate(1 / interarrival_time)
            yield self.envSimpy.timeout(self.IAT)
        
        # After all the products are put into the store, start process 2
        # Process 2 - Getting products from the store and create machine request
        self.envSimpy.process(self.process_2())
    
    # -----------------------------PROCESS 2-------------------------------------------------  
    def process_2(self): # If machine.queue is less than 4, get a prod from store and create request
        while True:
            if len(self.machine.queue) < self.QUEUE_LENGTH:
                
                # Get product from store
                prod = yield self.store.get()
                
                # Request machine
                req = prod.machine.request()

                self.envSimpy.process(self.process_3(prod, req))
            else:
                yield self.envSimpy.timeout(1)

    # -----------------------------PROCESS 3-------------------------------------------------  
    def process_3(self,prod, req): # Wait for req to go through and then produce and release the machine  
        sim.prod_and_requests.append([prod,req])
        # Wait for the request to succeed
        yield req
        
        
        #Setup process if required
        print("setup time ### ",self.machine1_prev_type , prod.prod_type )
        if self.machine1_prev_type == 0:
            pass # dont' do anything during the first pass
        elif self.machine1_prev_type == prod.prod_type:
            pass # Dont' do anything if the product types are the same 
        elif prod.prod_type == 2: # current product type = 2 meaning we have to do a changeover
            print("Setup time prod1 to prod2 " )
            yield env.timeout(self.P1_to_P2)
        elif prod.prod_type == 1: # current product type = 2 meaning we have to do a changeover
            print("Setup time prod2 to prod1 " )
            yield env.timeout(self.P2_to_P1)
        else:
            raise Exception("Sorry product type doesn't match available values [for Setup process]")
        
        
        # ----------------------------
        
        print('Start production of ' + str(prod.name) + ' at '+ str(self.envSimpy.now)  )

        print('Production time is ' + str(prod.production_time))
        yield self.envSimpy.timeout(prod.production_time)
        
        # Changing the previous prod_type on the machine
        self.machine1_prev_type == prod.prod_type
        
        prod.tardiness = self.envSimpy.now - prod.production_end   # -ve is good; +ve is bad 
        
        
        # End of production 
        print('End production of ' + str(prod.name) + ' at ' + str(self.envSimpy.now))


        # Wait for an acceptance only when there are products in the machine.queue
        if (sim.machine.queue) != []:
            # Pass time when the action chosen by the agent is rejection
            i = 0
            while True:
                if i == 0:
                    yield self.envSimpy.timeout(1)
                i += 1

                #print("Inside current_action", sim.current_action)

                if sim.current_action == 1: #rejected

                    # rearrange the machine queue to reflect the rejection
                    sim.machine.queue.insert(len(sim.machine.queue), sim.machine.queue.pop(0))
                    print("Action rejected; Passing time by 1 ", i)
                    print("Machine queue,prod types ", sim.machine.queue, sim.getObs())
                    print("Current time " + str(self.envSimpy.now))
                    print("Machine product type ",)
                    print("Queue item 1 product type ", )
                    yield self.envSimpy.timeout(1)




                    # rearrange the machine queue to reflect the rejection
                    #self.machine.queue.insert(len(self.machine.queue), self.machine.queue.pop(0))


                    # print the rearranged machine queue
                    #print('#observation_after')
                    #print(envGym.getObservation())



                else: #if action accepted
                    print("Action accepted")
                    break
        else:
            pass


        # Decide the reward 
        if prod.tardiness <= 0:
            sim.reward = 10 
        else: 
            sim.reward = 0

        print("Tardiness is ",prod.tardiness)
        # Production has ended now I have to take the next action using take_action()
        # envGym.machine.queue = envGym.take_action()
        #envGym.machine.queue = []

        # Release the machine
        #yield prod.machine.release(req)
        
        # Release the machine
        yield prod.machine.release(req)
        print(len(self.machine.queue))

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
        print("------ obs ", tuple(obs))
        
        return tuple(obs)
    
    def time_left(self, due):
        return (due - sim.envSimpy.now)
    
    def time_convert(self, time):
        time_max = self.TIME_MAX
        time_min = self.TIME_MIN
        
        if time_min < time <= time_max:
            min_max_time = (time-time_min)/(time_max-time_min)
            scaled_time = min_max_time * 10 # Scaling time to be between 0 and 20
            return int(np.ceil(scaled_time))
        else:
            raise Exception("Input time value outside range in def time_convert")
    
     
    def encode(self, obs):
        print('Entered encode')
        # (3), 3 [Machine queue type, machine product type]
        i = obs[0] 
        i *= 3
        
        i += obs[1]
        print("Value of i inside encode ", i)
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
        if lenQueue == 0 and lenMachinesUsed == 0: 
            #print("length of queue ",lenQueue,"Machines used ", lenMachinesUsed)
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
        print("Entered Reset")
        # Initialise simpy environemnt and a machine
        self.envSimpy = simpy.Environment()
        self.machine = simpy.Resource(self.envSimpy,capacity = 1)
        self.store = simpy.Store(self.envSimpy) 
        
        # Initial variable definitions
        self.time_start = self.envSimpy.now
        self.next_time_stop = self.time_start + 1
        self.time_step = 0.99 
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
        #print("machine is used by",sim.machine.users)
        # Run for time_step
        self.next_time_stop += self.time_step
        self.envSimpy.run(until = self.next_time_stop)
    
        # Get values
        observation = self.getObs()
        done = self.doneFn()
        info = self.info
        self.cumulative_reward += self.reward
        print("Values from Step",observation, sim.reward, done, info)
        # Return values
        return (observation, sim.reward, done, info)

        
    class product(object):
        def __init__(self, flowshopGym, envSimpy, name, number, machine):
            
            # Creating the required resources and environment
            self.envSimpy = envSimpy

            # State space variables
            self.prod_type = random.randint(1,2) # the product type of the product.
            
            
            
            # Rest of the variables
            
            self.prod_state = 1 # the state of production. 1 implies raw material. 2 implies first operation done and so on. 
            self.production_time = random.randint(1,8)
            self.production_end = self.production_time + random.randint(20,90)
            self.name = name
            self.number = number
            self.machine = machine 
            #self.production()
            #self.envSimpy.process(self.production())
            
            # putting the product into the store
            self.envSimpy.process(self.put_store())
 

        def put_store(self):
            yield sim.envSimpy.timeout(1)
            print("Putting the", self.name, "in the store ")
            sim.store.put(self)
            print("Items in the store",len(sim.store.items))
            
        