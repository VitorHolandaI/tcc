import ENDPOINTS from "./Endpoints";
import ApiMethods from "./ApiMethods";

class ApiManagerProva {
	static updateProva = (userid:string,provaid:number,params:string) => {
		const url = ENDPOINTS.PROVA_DETAIL(userid,provaid);
		return ApiMethods.put(url,params);
	}
}
export default ApiManagerProva;
