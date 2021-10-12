package com.oci.fn.example;

import java.net.MalformedURLException;
import java.net.URI;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import org.apache.http.HttpEntity;
import org.apache.http.HttpHeaders;
import org.apache.http.HttpHost;
import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.AuthCache;
import org.apache.http.client.CredentialsProvider;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.protocol.HttpClientContext;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.auth.BasicScheme;
import org.apache.http.impl.client.BasicAuthCache;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.json.JSONArray;
import org.json.JSONObject;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.fnproject.fn.api.httpgateway.HTTPGatewayContext;

public class ATPORDSClient {

	private static String ORDS_BASE_URL;
	private static String DB_USER;
	private static String DB_PASSWORD;

	@FnConfiguration
	public void setUp(RuntimeContext ctx) throws Exception {
		ORDS_BASE_URL = ctx.getConfigurationByKey("ORDS_BASE_URL").get();
		DB_USER = ctx.getConfigurationByKey("DB_USER").get();
		DB_PASSWORD = ctx.getConfigurationByKey("DB_PASSWORD").get();

	}

	public static class ProductItem {
		public final String name;
		public final int count;

		public ProductItem(String name, int count) {
			super();
			this.name = name;
			this.count = count;
		}

	}

	public static class RestApiResult {
		private int statusCode;
		private List<ProductItem> results;

		public int getStatusCode() {
			return statusCode;
		}

		public void setStatusCode(int statusCode) {
			this.statusCode = statusCode;
		}

		public RestApiResult(List<ProductItem> results) {
			super();
			this.results = results;
		}

		public List<ProductItem> getResults() {
			return results;
		}

	}

	public RestApiResult handleRequest(HTTPGatewayContext hctx) throws Exception {
		String requestUrl = hctx.getRequestURL();
		System.out.println("Request URL: " + requestUrl);
		try {
			List<NameValuePair> queryParams = URLEncodedUtils.parse(new URI(requestUrl), Charset.forName("UTF-8"));
			String sqlQuery = getSqlQueryString(requestUrl, queryParams);
			System.out.println("SQL query to be executed: " + sqlQuery);
			return invokeOrdsUrl(sqlQuery);
		} catch (MalformedURLException e) {
			System.out.print("Error occurred while parsing the request URL");
			e.printStackTrace();
			throw e;
		}
	}

	private RestApiResult invokeOrdsUrl(String sqlQuery) throws Exception {
		String ordsEndPoint = ORDS_BASE_URL + DB_USER + "/_/sql";
		URI ordsURI = new URI(ordsEndPoint);
		final HttpHost targetHost = new HttpHost(ordsURI.getHost(), 443, "https");
		CredentialsProvider credsProvider = new BasicCredentialsProvider();
		UsernamePasswordCredentials credentials = new UsernamePasswordCredentials(DB_USER, DB_PASSWORD);
		credsProvider.setCredentials(AuthScope.ANY, credentials);
		final AuthCache authCache = new BasicAuthCache();
		authCache.put(targetHost, new BasicScheme());

		RequestConfig.Builder requestBuilder = RequestConfig.custom();
		requestBuilder = requestBuilder.setAuthenticationEnabled(true);

		// Add AuthCache to the execution context
		final HttpClientContext context = HttpClientContext.create();
		context.setCredentialsProvider(credsProvider);
		context.setAuthCache(authCache);
		HttpClient httpclient = HttpClients.custom().setDefaultRequestConfig(requestBuilder.build())
				.setDefaultCredentialsProvider(credsProvider).build();
		HttpPost postRequest = new HttpPost(ordsEndPoint);
		postRequest.addHeader(HttpHeaders.CONTENT_TYPE, "application/sql");
		StringEntity requestEntity = new StringEntity(sqlQuery, "UTF-8");
		postRequest.setEntity(requestEntity);
		System.out.println("Executing request " + postRequest.getRequestLine());
		HttpResponse response = httpclient.execute(postRequest, context);
		int statusCode = response.getStatusLine().getStatusCode();
		System.out.println("response status code:" + statusCode);
		System.out.println(response.getStatusLine().getReasonPhrase());
		List<ProductItem> productItems = new ArrayList<ProductItem>();
		RestApiResult restApiResult = new RestApiResult(productItems);
		restApiResult.setStatusCode(statusCode);
		if (statusCode == 200) {
			HttpEntity entity = response.getEntity();
			String json = EntityUtils.toString(entity, StandardCharsets.UTF_8);
			System.out.println("Result of the ORDS Rest API" + json);

			JSONObject restResultObject = new JSONObject(json);
			if (restResultObject.has("items")) {
				JSONObject resultItemJson = (JSONObject) restResultObject.getJSONArray("items").iterator().next();
				if (resultItemJson != null && resultItemJson.has("resultSet")) {
					JSONObject resultSetObject = resultItemJson.getJSONObject("resultSet");
					if (resultSetObject.has("items")) {
						JSONArray itemsArray = resultSetObject.getJSONArray("items");

						for (Object jsonObject : itemsArray) {
							JSONObject productItemObject = (JSONObject) jsonObject;
							String productName = productItemObject.getString("name");
							int productCount = productItemObject.getInt("count");
							productItems.add(new ProductItem(productName, productCount));
						}
					}
				}
			}
		}
		return restApiResult;

	}

	private String getSqlQueryString(String requestUrlPath, List<NameValuePair> queryParams) {
		String tableName = DB_USER + ".products";
		String sqlQuery = null;
		String productName = null;
		String productCount = null;
		if (queryParams != null) {
			for (NameValuePair queryParam : queryParams) {
				if (queryParam.getName().equals("name")) {
					productName = queryParam.getValue();
					continue;
				}
				if (queryParam.getName().equals("count")) {
					productCount = queryParam.getValue();
					continue;
				}
			}
		}
		if (requestUrlPath.startsWith("/getProducts")) {
			sqlQuery = "select name, count from " + tableName;
		} else if (requestUrlPath.startsWith("/addProduct")) {
			sqlQuery = "insert into " + tableName + " values ('" + productName + "' , " + productCount + ")";
		} else if (requestUrlPath.startsWith("/updateProduct")) {
			sqlQuery = "update " + tableName + " set count=" + productCount + " where name = '" + productName + "'";
		} else if (requestUrlPath.startsWith("/deleteProduct")) {
			sqlQuery = "delete from " + tableName + " where name = '" + productName + "'";
		}

		return sqlQuery;
	}


}
