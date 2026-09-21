use std::sync::Arc;

use url_shortener::app::build_app;
use url_shortener::store::Store;

#[tokio::main]
async fn main() {
    let base_url = url_shortener::config::base_url_from_env().unwrap_or_else(|err| {
        eprintln!("{err}");
        std::process::exit(1);
    });

    let app = build_app(base_url, Arc::new(Store::new()));

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8080);
    let listener = tokio::net::TcpListener::bind(("0.0.0.0", port)).await.unwrap();
    println!("listening on {}", listener.local_addr().unwrap());
    axum::serve(listener, app).await.unwrap();
}
