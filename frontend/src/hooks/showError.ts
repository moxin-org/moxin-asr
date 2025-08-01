import { reactive} from 'vue'
const toggleError = reactive({show:false, title:'error',msg:'Failed to connect to server'})
export  {toggleError}