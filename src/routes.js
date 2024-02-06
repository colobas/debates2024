import HomePage from './HomePage.svelte'
import Debate from './Debate.svelte'

// Export the route definition object
export const routes = {
    '/debate/:slug': Debate,
    '/': HomePage,
}
